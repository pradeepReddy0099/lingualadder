// LinguaLadder interface text in English and Spanish (the search language and the interface language are independent).
(function (root) {
  const D = {
    en: {
      title: 'LinguaLadder: Wikipedia at your reading level',
      h1: 'Read Wikipedia at <em>your</em> level.',
      lede: "Search in the language you're learning. Results are ranked by what they're about <em>and</em> by how well they fit your reading level.",
      search: 'Search', search_ph: 'Search a topic: volcano, chocolate, fútbol…', search_key: 'Press / to search',
      language: 'Language', your_level: 'Your level', interface: 'Interface',
      lv_beginner_opt: 'Beginner (A1–A2)', lv_intermediate_opt: 'Intermediate (B1–B2)', lv_advanced_opt: 'Advanced (C1+)',
      lv_custom_opt: 'My placement result ({cefr})', lv_custom_plain: 'My placement result',
      find_level: 'Find my level', display_options: 'Display options',
      cmp: 'Compare with plain search', big_text: 'Large text', plain: 'Ignore my level (plain BM25)',
      topics_h: 'Recommended topics', topics_sub: 'picked for your level',
      step1_h: 'Find your level', step1_p: 'A three-minute test: a vocabulary check, then short passages that adapt to your answers.',
      step2_h: 'Search any topic', step2_p: 'On-topic articles come first, ranked toward your level. Passing mentions sink to the bottom.',
      step3_h: 'Climb the ladder', step3_p: "Each result shows a level and CEFR band, so you can step up when you're ready.",
      footer: 'Runs entirely in your browser: BM25, a topic guard, and a level-fit reranker over a Wikipedia index (English and Spanish). Article text CC BY-SA.',
      test_title: 'Find your level', close: 'Close',
      lang_en: 'English', lang_es: 'Spanish',
      lvl_beginner: 'Beginner', lvl_intermediate: 'Intermediate', lvl_advanced: 'Advanced',
      b_beginner: 'beginner', b_intermediate: 'intermediate', b_advanced: 'advanced',
      chip: 'Your level: {cefr} · {level}',
      loading: 'Loading index…', no_results: 'No results',
      empty: 'No matches. Try a simpler or different word, or pick a recommended topic.',
      results_in: '{n} results in {ms} ms', plain_tag: ' (plain BM25)', fitted: ' fitted to {level}', fitted_custom: 'your placement level',
      all_mention: ' · No articles are mainly about this yet; these only mention it.',
      some_mention: ' · {on} about this topic, then {off} that only mention it.',
      mentions: 'mentions', mentions_title: 'Mentions the search words but is not mainly about them', read_badge: 'read',
      relevance: 'relevance', level_fit: 'level fit', words: '{n} words', read_on: 'Read on Wikipedia', read_next: 'Read next ↑',
      too_easy: 'Too easy', too_hard: 'Too hard',
      plain_bm25: 'Plain BM25', ll_col: 'LinguaLadder ({level})',
      ladder_h: 'The ladder for this topic', ladder_none: 'No article at this level yet',
      next_up: 'Next up:', nothing_harder: '(nothing harder left on this topic)',
      all_read: 'You have read everything on this topic. Try a recommended topic.',
      all_topics: 'All {n} topics', fewer_topics: 'Show fewer',
      fb_up: 'Got it, stepping your level up.', fb_down: 'Got it, stepping your level down.',
      load_err: 'Could not load the {lang} index',
      t_intro_h: '{lang} placement · about 3 minutes',
      t_intro_p: "Two short parts. First, tap the words you know. Some are made up, so only tap the ones you're sure of. Then fill the blank in a few passages. They get harder or easier as you go.",
      t_start: 'Start', t_vocab_h: 'Which of these words do you know?', t_vocab_p: 'Tap every word you could explain or translate. Leave the rest.',
      t_continue: 'Continue', t_cloze_h: 'Fill the blank', t_of: '{i} of {n}', t_skip: "I don't know",
      t_res_lead: 'Your reading level in {lang}',
      t_res_detail: '{level} · vocabulary {vocab}% · reading at the {pct}th percentile of articles. Results now aim at this level, and "Too easy" or "Too hard" on any article fine-tunes it.',
      t_done: 'Start reading'
    },
    es: {
      title: 'LinguaLadder: Wikipedia a tu nivel de lectura',
      h1: 'Lee Wikipedia a <em>tu</em> nivel.',
      lede: 'Busca en el idioma que estás aprendiendo. Los resultados se ordenan por el tema <em>y</em> por lo bien que encajan con tu nivel de lectura.',
      search: 'Buscar', search_ph: 'Busca un tema: volcán, chocolate, fútbol…', search_key: 'Pulsa / para buscar',
      language: 'Idioma', your_level: 'Tu nivel', interface: 'Interfaz',
      lv_beginner_opt: 'Principiante (A1–A2)', lv_intermediate_opt: 'Intermedio (B1–B2)', lv_advanced_opt: 'Avanzado (C1+)',
      lv_custom_opt: 'Mi resultado de nivel ({cefr})', lv_custom_plain: 'Mi resultado de nivel',
      find_level: 'Descubre mi nivel', display_options: 'Opciones de pantalla',
      cmp: 'Comparar con la búsqueda simple', big_text: 'Texto grande', plain: 'Ignorar mi nivel (BM25 simple)',
      topics_h: 'Temas recomendados', topics_sub: 'elegidos para tu nivel',
      step1_h: 'Descubre tu nivel', step1_p: 'Una prueba de tres minutos: un test de vocabulario y luego textos cortos que se adaptan a tus respuestas.',
      step2_h: 'Busca cualquier tema', step2_p: 'Primero salen los artículos sobre el tema, ordenados según tu nivel. Las menciones de pasada quedan al final.',
      step3_h: 'Sube la escalera', step3_p: 'Cada resultado muestra un nivel y una banda del MCER, para que subas cuando estés listo.',
      footer: 'Funciona por completo en tu navegador: BM25, un filtro de tema y un reordenador por nivel sobre un índice de Wikipedia (inglés y español). Texto de los artículos bajo CC BY-SA.',
      test_title: 'Descubre tu nivel', close: 'Cerrar',
      lang_en: 'inglés', lang_es: 'español',
      lvl_beginner: 'Principiante', lvl_intermediate: 'Intermedio', lvl_advanced: 'Avanzado',
      b_beginner: 'principiante', b_intermediate: 'intermedio', b_advanced: 'avanzado',
      chip: 'Tu nivel: {cefr} · {level}',
      loading: 'Cargando el índice…', no_results: 'Sin resultados',
      empty: 'Sin coincidencias. Prueba con una palabra más simple o distinta, o elige un tema recomendado.',
      results_in: '{n} resultados en {ms} ms', plain_tag: ' (BM25 simple)', fitted: ' ajustados a {level}', fitted_custom: 'tu nivel de la prueba',
      all_mention: ' · Todavía no hay artículos centrados en esto; estos solo lo mencionan.',
      some_mention: ' · {on} sobre este tema y luego {off} que solo lo mencionan.',
      mentions: 'menciona', mentions_title: 'Menciona las palabras buscadas, pero no trata principalmente de ellas', read_badge: 'leído',
      relevance: 'relevancia', level_fit: 'ajuste al nivel', words: '{n} palabras', read_on: 'Leer en Wikipedia', read_next: 'Leer a continuación ↑',
      too_easy: 'Muy fácil', too_hard: 'Muy difícil',
      plain_bm25: 'BM25 simple', ll_col: 'LinguaLadder ({level})',
      ladder_h: 'La escalera de este tema', ladder_none: 'Aún no hay artículo de este nivel',
      next_up: 'Siguiente:', nothing_harder: '(no queda nada más difícil sobre este tema)',
      all_read: 'Ya has leído todo sobre este tema. Prueba con un tema recomendado.',
      all_topics: 'Los {n} temas', fewer_topics: 'Ver menos',
      fb_up: 'Entendido, subo tu nivel.', fb_down: 'Entendido, bajo tu nivel.',
      load_err: 'No se pudo cargar el índice de {lang}',
      t_intro_h: 'Prueba de nivel de {lang} · unos 3 minutos',
      t_intro_p: 'Dos partes cortas. Primero, toca las palabras que conoces. Algunas son inventadas, así que toca solo las que tengas claras. Después, completa el hueco en unos pocos textos. Se vuelven más difíciles o más fáciles según tus respuestas.',
      t_start: 'Empezar', t_vocab_h: '¿Cuáles de estas palabras conoces?', t_vocab_p: 'Toca cada palabra que sepas explicar o traducir. Deja las demás.',
      t_continue: 'Continuar', t_cloze_h: 'Completa el hueco', t_of: '{i} de {n}', t_skip: 'No lo sé',
      t_res_lead: 'Tu nivel de lectura en {lang}',
      t_res_detail: '{level} · vocabulario {vocab}% · lees al nivel del percentil {pct} de los artículos. Ahora los resultados apuntan a este nivel, y «Muy fácil» o «Muy difícil» en cualquier artículo lo afina.',
      t_done: 'Empezar a leer'
    }
  };
  let cur = 'en';
  const api = {
    dict: D,
    langs: Object.keys(D),
    get: () => cur,
    set: l => { if (D[l]) cur = l; return cur; },
    detect: nav => (String(nav || '').toLowerCase().startsWith('es') ? 'es' : 'en'),
    t(k, vars) {
      let s = (D[cur] && D[cur][k]) ?? D.en[k] ?? k;
      if (vars) for (const [a, b] of Object.entries(vars)) s = s.split('{' + a + '}').join(b);
      return s;
    },
    // Fill every [data-i18n] (text), [data-i18n-html], [data-i18n-ph], [data-i18n-title], [data-i18n-aria] in the page.
    apply(doc) {
      if (!doc || !doc.querySelectorAll) return;
      const each = (attr, fn) => doc.querySelectorAll('[' + attr + ']').forEach(el => fn(el, el.getAttribute(attr)));
      each('data-i18n', (el, k) => {
        const nodes = [...el.childNodes].filter(n => n.nodeType === 3 && n.textContent.trim());
        if (nodes.length) nodes[nodes.length - 1].textContent = ' ' + api.t(k) + ' '; else el.textContent = api.t(k);
      });
      each('data-i18n-html', (el, k) => { el.innerHTML = api.t(k); });
      each('data-i18n-ph', (el, k) => el.setAttribute('placeholder', api.t(k)));
      each('data-i18n-title', (el, k) => el.setAttribute('title', api.t(k)));
      each('data-i18n-aria', (el, k) => el.setAttribute('aria-label', api.t(k)));
      if (doc.documentElement) doc.documentElement.setAttribute('lang', cur);
      doc.title = api.t('title');
    }
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.LLI18n = api;
})(typeof self !== 'undefined' ? self : this);
