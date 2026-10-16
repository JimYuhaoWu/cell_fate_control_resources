/*
 * app.js — renders the catalogue from site/data/*.json.
 *
 * No framework, no bundler, no build step: the exported JSON is the only
 * input, and `scripts/07_export_site.py` is the only thing that produces it.
 */
(function () {
  'use strict';

  // --- copy, not data -------------------------------------------------------
  // The four axis values come from the data; the questions they answer are the
  // editorial half of schema §5.
  var AXIS_QUESTION = {
    'where': 'Where on the genome do I act?',
    'what': 'What do I perturb, with what cell-level effect?',
    'how': 'How do I represent and score sequence?',
    'with-what': 'What do I build the actuator from?'
  };
  var AXIS_ORDER = ['where', 'what', 'how', 'with-what'];

  // Facet columns the panel leads with; everything else follows alphabetically.
  var FACET_ORDER = ['type', 'evidence_tier', 'availability_tier', 'organism',
    'assay', 'task', 'architecture', 'model_family', 'license'];

  // Bookkeeping and identifier columns: real columns, but nobody filters by
  // them. fate_axis is excluded because it is the primary navigation above.
  var FACET_SKIP = ['fate_axis', 'aliases', 'curator', 'date_added',
    'date_updated', 'supersedes', 'variant_of', 'ecr_lib_source_key',
    'protocol_doi', 'canonical_host', 'version', 'status'];

  // Columns whose array values filter by membership rather than equality.
  // Derived from the data: a column is array-valued if any entity holds an
  // array in it.
  var ARRAY_COLUMNS = {};

  var PAPER_ROLE_NOTE = {
    'primary': 'the paper the resource is from',
    'preprint': 'earlier version of the primary paper',
    'benchmark': 'evaluates it',
    'critique': 'evaluates it and reports a limitation',
    'application': 'uses it',
    'extension': 'builds on it',
    'review': 'surveys it'
  };

  var state = {
    axis: null,
    filters: {},          // column -> [values]
    query: '',
    entities: [],
    papers: {},
    facets: {}
  };

  // --- data ----------------------------------------------------------------

  function load() {
    return Promise.all(['entities', 'facets', 'papers'].map(function (name) {
      return fetch('data/' + name + '.json').then(function (r) {
        if (!r.ok) { throw new Error('data/' + name + '.json: ' + r.status); }
        return r.json();
      });
    }));
  }

  function searchText(entity) {
    var parts = [entity.name, (entity.aliases || []).join(' '),
      (entity.tags || []).join(' '), entity.description, entity.notes];
    (entity.papers || []).forEach(function (p) {
      var paper = state.papers[p.paper_id];
      parts.push(p.title);
      if (paper) { parts.push(paper.abstract); }
    });
    return parts.filter(Boolean).join(' ');
  }

  // --- filtering -----------------------------------------------------------

  function holds(entity, column, values) {
    var cell = entity[column];
    if (cell == null) { return false; }
    if (ARRAY_COLUMNS[column]) {
      var list = Array.isArray(cell) ? cell : [cell];
      return values.some(function (v) { return list.indexOf(v) !== -1; });
    }
    return values.indexOf(String(cell)) !== -1;
  }

  function matches(entity, skipColumn) {
    if (state.axis && (entity.fate_axis || []).indexOf(state.axis) === -1) {
      return false;
    }
    return Object.keys(state.filters).every(function (column) {
      if (column === skipColumn || !state.filters[column].length) { return true; }
      return holds(entity, column, state.filters[column]);
    });
  }

  function selected() {
    var hits = state.entities.filter(function (e) { return matches(e); });
    if (!state.query.trim()) {
      return hits.sort(function (a, b) { return a.name.localeCompare(b.name); });
    }
    var ranked = window.CFCRSearch.rank(state.query, hits.map(function (e) {
      return e.entity_id;
    }));
    var byId = {};
    hits.forEach(function (e) { byId[e.entity_id] = e; });
    return (ranked || []).map(function (hit) { return byId[hit.id]; })
      .filter(Boolean);
  }

  // --- rendering helpers ---------------------------------------------------

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) { node.className = className; }
    if (text != null) { node.textContent = text; }
    return node;
  }

  function label(value) {
    if (value === '1') { return 'yes'; }
    if (value === '0') { return 'no'; }
    return String(value);
  }

  function humanize(column) {
    return column.replace(/_/g, ' ').replace(/\bn /, 'number of ');
  }

  // --- axis navigation -----------------------------------------------------

  function renderAxes() {
    var grid = document.getElementById('axis-grid');
    grid.textContent = '';
    var values = (state.facets.fate_axis || []).slice().sort(function (a, b) {
      return AXIS_ORDER.indexOf(a) - AXIS_ORDER.indexOf(b);
    });

    values.concat([null]).forEach(function (axis) {
      var n = state.entities.filter(function (e) {
        return axis === null || (e.fate_axis || []).indexOf(axis) !== -1;
      }).length;
      var button = el('button', 'axis' + (axis === null ? ' axis-all' : '')
        + (state.axis === axis ? ' on' : ''));
      button.type = 'button';
      button.setAttribute('aria-pressed', String(state.axis === axis));
      button.appendChild(el('span', 'axis-name', axis === null ? 'everything' : axis));
      button.appendChild(el('span', 'axis-q', axis === null
        ? 'All six resource types, unfiltered'
        : AXIS_QUESTION[axis] || ''));
      button.appendChild(el('span', 'axis-n', n + ' resource' + (n === 1 ? '' : 's')));
      button.addEventListener('click', function () {
        state.axis = axis;
        location.hash = axis === null ? '' : axis;
        render();
      });
      grid.appendChild(button);
    });
  }

  // --- facet panel ---------------------------------------------------------

  function renderFacets() {
    var host = document.getElementById('facet-list');
    host.textContent = '';

    var columns = Object.keys(state.facets).filter(function (column) {
      if (FACET_SKIP.indexOf(column) !== -1) { return false; }
      // Numeric columns (context length, record counts, year) are real facets
      // in the loader but useless as equality checkboxes.
      return !state.facets[column].every(function (v) {
        return typeof v === 'number';
      });
    }).sort(function (a, b) {
      var ia = FACET_ORDER.indexOf(a), ib = FACET_ORDER.indexOf(b);
      if (ia !== -1 || ib !== -1) {
        return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
      }
      return a.localeCompare(b);
    });

    columns.forEach(function (column, index) {
      // Counts respect every filter except this column's own, so a facet
      // never hides the values you could still add to it.
      var pool = state.entities.filter(function (e) {
        return matches(e, column);
      });
      var counts = {};
      state.facets[column].forEach(function (value) {
        counts[value] = pool.filter(function (e) {
          return holds(e, column, [String(value)]);
        }).length;
      });
      var live = state.facets[column].filter(function (v) {
        return counts[v] > 0 || (state.filters[column] || []).indexOf(String(v)) !== -1;
      });
      if (!live.length) { return; }

      var group = el('details', 'facet');
      if (index < 4 || (state.filters[column] || []).length) {
        group.open = true;
      }
      var head = el('summary', null, humanize(column));
      var chosen = (state.filters[column] || []).length;
      if (chosen) { head.appendChild(el('span', 'chosen', String(chosen))); }
      group.appendChild(head);

      live.forEach(function (value) {
        var row = el('label', 'check');
        var box = document.createElement('input');
        box.type = 'checkbox';
        box.value = String(value);
        box.checked = (state.filters[column] || []).indexOf(String(value)) !== -1;
        box.addEventListener('change', function () {
          var chosenValues = state.filters[column] || [];
          state.filters[column] = box.checked
            ? chosenValues.concat([box.value])
            : chosenValues.filter(function (v) { return v !== box.value; });
          render();
        });
        row.appendChild(box);
        row.appendChild(el('span', 'check-name', label(value)));
        row.appendChild(el('span', 'check-n', String(counts[value])));
        group.appendChild(row);
      });
      host.appendChild(group);
    });
  }

  // --- cards ---------------------------------------------------------------

  function firstAuthor(authors) {
    if (!authors || !authors.length) { return ''; }
    return authors.length > 1 ? authors[0] + ' et al.' : authors[0];
  }

  function evidenceBlock(entity) {
    var box = el('div', 'evidence');
    var badge = el('span', 'badge ev ' + entity.evidence_tier,
      entity.evidence_tier);
    box.appendChild(badge);

    var evaluating = (entity.papers || []).filter(function (p) {
      return ['benchmark', 'critique', 'review', 'extension'].indexOf(p.role) !== -1;
    });
    if (!evaluating.length) {
      box.appendChild(el('p', 'ev-none',
        'No evaluation by anyone outside the originating group is recorded.'));
      return box;
    }
    box.appendChild(el('p', 'ev-head', 'Evaluated by:'));
    var list = el('ul', 'ev-list');
    evaluating.forEach(function (p) {
      var item = el('li');
      item.appendChild(el('span', 'role ' + p.role, p.role));
      var paper = state.papers[p.paper_id] || {};
      var link = el('a', null, p.title || p.paper_id);
      link.href = paper.url || ('https://doi.org/' + p.paper_id);
      link.rel = 'noopener';
      item.appendChild(link);
      item.appendChild(el('span', 'byline',
        ' ' + firstAuthor(paper.authors) + (p.year ? ', ' + p.year : '')));
      if (p.note) { item.appendChild(el('p', 'ev-note', p.note)); }
      list.appendChild(item);
    });
    box.appendChild(list);
    return box;
  }

  function availabilityBlock(entity) {
    var box = el('div', 'availability');
    box.appendChild(el('span', 'badge av ' + entity.availability_tier,
      entity.availability_tier));
    box.appendChild(el('span', 'licence' + (entity.license ? '' : ' licence-none'),
      entity.license ? entity.license : 'no licence stated'));
    return box;
  }

  function trailBlock(entity) {
    var box = el('details', 'trail');
    var papers = entity.papers || [];
    box.appendChild(el('summary', null,
      'Evidence trail — ' + papers.length + ' paper' + (papers.length === 1 ? '' : 's')));
    var list = el('ul', 'trail-list');
    papers.forEach(function (p) {
      var paper = state.papers[p.paper_id] || {};
      var item = el('li');
      item.appendChild(el('span', 'role ' + p.role, p.role));
      var link = el('a', null, p.title || p.paper_id);
      link.href = paper.url || ('https://doi.org/' + p.paper_id);
      link.rel = 'noopener';
      item.appendChild(link);
      item.appendChild(el('span', 'byline', ' ' + firstAuthor(paper.authors)
        + (p.year ? ', ' + p.year : '') + (paper.venue ? ', ' + paper.venue : '')));
      item.appendChild(el('span', 'role-gloss', ' — ' + (PAPER_ROLE_NOTE[p.role] || '')));
      if (p.note) { item.appendChild(el('p', 'ev-note', p.note)); }
      list.appendChild(item);
    });
    box.appendChild(list);
    return box;
  }

  function fieldsBlock(entity) {
    var box = el('details', 'fields');
    box.appendChild(el('summary', null, 'All catalogued fields'));
    var table = el('table', 'field-table');
    Object.keys(entity).sort().forEach(function (column) {
      if (['papers', 'name', 'description', 'notes', 'entity_id',
        'primary_paper_title'].indexOf(column) !== -1) { return; }
      var row = el('tr');
      row.appendChild(el('th', null, humanize(column)));
      var cell = Array.isArray(entity[column])
        ? entity[column].join(', ') : label(entity[column]);
      row.appendChild(el('td', null, cell));
      table.appendChild(row);
    });
    box.appendChild(table);
    return box;
  }

  function card(entity) {
    var node = el('article', 'card');
    node.id = entity.entity_id;

    var head = el('header', 'card-head');
    head.appendChild(el('h3', null, entity.name));
    head.appendChild(el('span', 'type ' + entity.type, entity.type));
    if (entity.year) { head.appendChild(el('span', 'year', String(entity.year))); }
    node.appendChild(head);

    var axes = el('p', 'card-axes');
    (entity.fate_axis || []).forEach(function (axis) {
      axes.appendChild(el('span', 'chip axis-chip', axis));
    });
    node.appendChild(axes);

    // Badges before the prose: anyone reusing a resource has to see the
    // licence and the evidence before they see the paper.
    var badges = el('div', 'badges');
    if (entity.availability_tier) { badges.appendChild(availabilityBlock(entity)); }
    if (entity.validation_tier) {
      badges.appendChild(el('span', 'badge va', 'validation: ' + entity.validation_tier));
    }
    if (badges.childNodes.length) { node.appendChild(badges); }
    if (entity.evidence_tier) { node.appendChild(evidenceBlock(entity)); }

    if (entity.description) {
      node.appendChild(el('p', 'desc', entity.description.trim()));
    }
    if (entity.notes) {
      var notes = el('details', 'curator-notes');
      notes.appendChild(el('summary', null, 'Curator note'));
      notes.appendChild(el('p', null, entity.notes.trim()));
      node.appendChild(notes);
    }

    var tags = el('p', 'card-tags');
    (entity.tags || []).forEach(function (tag) {
      tags.appendChild(el('span', 'chip', tag));
    });
    node.appendChild(tags);

    if ((entity.papers || []).length) { node.appendChild(trailBlock(entity)); }
    node.appendChild(fieldsBlock(entity));
    return node;
  }

  // --- render --------------------------------------------------------------

  function render() {
    var hits = selected();
    var cards = document.getElementById('cards');
    cards.textContent = '';
    hits.forEach(function (entity) { cards.appendChild(card(entity)); });
    document.getElementById('empty').hidden = hits.length > 0;

    var active = Object.keys(state.filters).filter(function (c) {
      return state.filters[c].length;
    }).length;
    document.getElementById('count').textContent =
      hits.length + ' of ' + state.entities.length + ' resources'
      + (state.axis ? ' on the "' + state.axis + '" axis' : '')
      + (active ? ', ' + active + ' filter' + (active === 1 ? '' : 's') + ' applied' : '')
      + (state.query.trim() ? ', ranked by relevance' : '');

    renderAxes();
    renderFacets();
  }

  function axisFromHash() {
    var hash = decodeURIComponent(location.hash.replace(/^#/, ''));
    return AXIS_ORDER.indexOf(hash) !== -1 ? hash : null;
  }

  function wire() {
    // On a phone the filter panel sits above the results, so it starts
    // collapsed: the cards are what should be on screen first.
    if (window.innerWidth < 900) {
      document.querySelector('.facet-panel').open = false;
    }
    var box = document.getElementById('q');
    box.addEventListener('input', function () {
      state.query = box.value;
      render();
    });
    document.getElementById('clear').addEventListener('click', function (event) {
      event.preventDefault();
      state.filters = {};
      state.query = '';
      box.value = '';
      render();
    });
    // Keeps the back button working across axis navigation.
    window.addEventListener('hashchange', function () {
      state.axis = axisFromHash();
      render();
    });
  }

  load().then(function (data) {
    state.entities = data[0];
    state.facets = data[1];
    data[2].forEach(function (paper) { state.papers[paper.paper_id] = paper; });

    state.entities.forEach(function (entity) {
      Object.keys(entity).forEach(function (column) {
        if (Array.isArray(entity[column])) { ARRAY_COLUMNS[column] = true; }
      });
    });

    window.CFCRSearch.build(state.entities.map(function (entity) {
      return { id: entity.entity_id, text: searchText(entity) };
    }));

    state.axis = axisFromHash();
    wire();
    render();
  }).catch(function (error) {
    document.getElementById('cards').appendChild(
      el('p', 'empty', 'Could not load the catalogue: ' + error.message));
  });
}());
