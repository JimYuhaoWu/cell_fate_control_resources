/*
 * search.js — client-side lexical search over the exported catalogue.
 *
 * One ranker ships: Okapi BM25 over each entity's searchable text (name,
 * aliases, tags, description, curator notes, and the titles and abstracts of
 * every attached paper).
 *
 * A second ranker — dense embeddings were the obvious candidate, see schema
 * §7 — is deliberately NOT built: with a 20-record corpus there is no way to
 * measure whether it helps, and it would cost a dependency plus a binary blob
 * in the repo. The seam it would plug into is `registerRanker` plus the marked
 * line in `rank`; see "Adding a second ranker" in the README.
 */
(function (global) {
  'use strict';

  var K1 = 1.2;    // term-frequency saturation
  var B = 0.75;    // length normalization

  // Only the words that would otherwise dominate short abstracts.
  var STOP = {};
  ('a an and are as at be been by for from has have in into is it its of on or'
    + ' that the their there these this to was were which with')
    .split(' ').forEach(function (w) { STOP[w] = true; });

  function tokenize(text) {
    return String(text == null ? '' : text)
      .toLowerCase()
      .split(/[^a-z0-9]+/)
      .filter(function (t) { return t.length > 1 && !STOP[t]; });
  }

  var RANKERS = {};

  function registerRanker(name, impl) {
    RANKERS[name] = impl;
  }

  /*
   * A ranker is { build(docs), score(queryTokens, ids) -> [{id, score}] },
   * where `docs` is [{ id, text }] and the returned list is sorted best-first
   * and carries only documents the ranker scored above zero.
   */
  function bm25Ranker() {
    var postings = {};     // term -> { id -> term frequency }
    var length = {};       // id -> token count
    var ids = [];
    var avgLength = 0;

    return {
      build: function (docs) {
        postings = {};
        length = {};
        ids = [];
        var total = 0;
        docs.forEach(function (doc) {
          var tokens = tokenize(doc.text);
          ids.push(doc.id);
          length[doc.id] = tokens.length;
          total += tokens.length;
          tokens.forEach(function (term) {
            var p = postings[term] || (postings[term] = {});
            p[doc.id] = (p[doc.id] || 0) + 1;
          });
        });
        avgLength = ids.length ? total / ids.length : 0;
      },

      score: function (queryTokens, candidates) {
        var allowed = null;
        if (candidates) {
          allowed = {};
          candidates.forEach(function (id) { allowed[id] = true; });
        }
        var n = ids.length;
        var scores = {};
        queryTokens.forEach(function (term) {
          var p = postings[term];
          if (!p) { return; }
          var df = Object.keys(p).length;
          var idf = Math.log(1 + (n - df + 0.5) / (df + 0.5));
          Object.keys(p).forEach(function (id) {
            if (allowed && !allowed[id]) { return; }
            var tf = p[id];
            var norm = tf + K1 * (1 - B + B * (length[id] / (avgLength || 1)));
            scores[id] = (scores[id] || 0) + idf * ((tf * (K1 + 1)) / norm);
          });
        });
        return Object.keys(scores)
          .map(function (id) { return { id: id, score: scores[id] }; })
          .sort(function (a, b) { return b.score - a.score; });
      }
    };
  }

  registerRanker('bm25', bm25Ranker());

  function build(docs) {
    Object.keys(RANKERS).forEach(function (name) {
      RANKERS[name].build(docs);
    });
  }

  /*
   * Rank `candidates` (entity ids that survived the facet pre-filter) for a
   * query string. `names` selects which registered rankers run.
   */
  function rank(query, candidates, names) {
    var queryTokens = tokenize(query);
    if (!queryTokens.length) { return null; }
    var lists = (names || ['bm25']).map(function (name) {
      return RANKERS[name].score(queryTokens, candidates);
    });
    // SEAM: with more than one ranker the lists are combined here — rank
    // fusion, weighted sum, whatever turns out to measure better. Nothing
    // measures anything on 20 records, so only the first list is used.
    return lists[0];
  }

  global.CFCRSearch = {
    tokenize: tokenize,
    registerRanker: registerRanker,
    build: build,
    rank: rank
  };
}(window));
