(() => {
  const $ = (id) => document.getElementById(id);
  const texto = $("texto");
  const btnMic = $("btn-mic");
  const btnCorregir = $("btn-corregir");
  const btnLimpiar = $("btn-limpiar");
  const btnEscuchar = $("btn-escuchar");
  const btnCopiar = $("btn-copiar");
  const btnUsar = $("btn-usar");
  const error = $("error");
  const resultado = $("resultado");
  const corregidoEl = $("corregido");
  const diffEl = $("diff");
  const resumen = $("resumen");
  const estado = $("estado");

  let ultimoCorregido = "";

  // ---------- Estado del modelo ----------
  async function revisarEstado() {
    try {
      const r = await fetch("/api/salud");
      const d = await r.json();
      estado.textContent = d.ok ? "Modelo listo" : "Modelo no disponible";
      estado.className = "estado " + (d.ok ? "ok" : "mal");
    } catch {
      estado.textContent = "Sin conexión";
      estado.className = "estado mal";
    }
  }
  revisarEstado();
  setInterval(revisarEstado, 30000);

  // ---------- Mensajes ----------
  function mostrarError(msg) {
    error.textContent = msg;
    error.hidden = !msg;
  }

  // ---------- Corregir ----------
  async function corregir() {
    const t = texto.value.trim();
    mostrarError("");
    if (!t) {
      mostrarError("Escribe o dicta algo primero.");
      texto.focus();
      return;
    }
    btnCorregir.disabled = true;
    btnCorregir.innerHTML = '<span class="cargando"></span> Corrigiendo…';
    try {
      const r = await fetch("/api/corregir", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texto: t }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || "No se pudo corregir el texto.");
      pintarResultado(d);
    } catch (e) {
      mostrarError(e.message || "Ocurrió un problema. Intenta de nuevo.");
    } finally {
      btnCorregir.disabled = false;
      btnCorregir.textContent = "Corregir";
    }
  }

  function pintarResultado(d) {
    ultimoCorregido = d.corregido;
    corregidoEl.textContent = d.corregido;
    diffEl.innerHTML = "";
    for (const seg of d.cambios) {
      if (seg.tipo === "igual") {
        diffEl.appendChild(document.createTextNode(seg.antes));
      } else {
        if (seg.antes.trim()) {
          const q = document.createElement("span");
          q.className = "quitado";
          q.textContent = seg.antes;
          diffEl.appendChild(q);
          diffEl.appendChild(document.createTextNode(" "));
        }
        if (seg.despues.trim()) {
          const a = document.createElement("span");
          a.className = "agregado";
          a.textContent = seg.despues;
          diffEl.appendChild(a);
        }
      }
    }
    if (d.num_cambios === 0) {
      resumen.textContent = "Sin errores, ¡bien escrito!";
      resumen.className = "chip sin-cambios";
    } else {
      resumen.textContent = d.num_cambios === 1 ? "1 corrección" : `${d.num_cambios} correcciones`;
      resumen.className = "chip";
    }
    resultado.hidden = false;
    resultado.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  btnCorregir.addEventListener("click", corregir);
  texto.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) corregir();
  });

  btnLimpiar.addEventListener("click", () => {
    texto.value = "";
    resultado.hidden = true;
    mostrarError("");
    window.speechSynthesis?.cancel();
    texto.focus();
  });

  btnUsar.addEventListener("click", () => {
    texto.value = ultimoCorregido;
    resultado.hidden = true;
    texto.focus();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  btnCopiar.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(ultimoCorregido);
      btnCopiar.textContent = "¡Copiado!";
      setTimeout(() => (btnCopiar.textContent = "Copiar"), 1500);
    } catch {
      mostrarError("No se pudo copiar. Selecciona el texto y cópialo manualmente.");
    }
  });

  // ---------- Leer en voz alta ----------
  function vozEspanol() {
    const voces = window.speechSynthesis.getVoices();
    return (
      voces.find((v) => v.lang === "es-MX") ||
      voces.find((v) => v.lang.startsWith("es")) ||
      null
    );
  }
  btnEscuchar.addEventListener("click", () => {
    if (!("speechSynthesis" in window)) {
      mostrarError("Este navegador no puede leer en voz alta.");
      return;
    }
    const synth = window.speechSynthesis;
    if (synth.speaking) {
      synth.cancel();
      return;
    }
    const u = new SpeechSynthesisUtterance(ultimoCorregido);
    u.lang = "es-MX";
    u.rate = 0.9;
    const voz = vozEspanol();
    if (voz) u.voice = voz;
    synth.speak(u);
  });

  // ---------- Dictado por voz ----------
  const Reconocimiento = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Reconocimiento) {
    btnMic.disabled = true;
    btnMic.title = "Este navegador no permite dictar (usa Chrome o Edge).";
  } else {
    const rec = new Reconocimiento();
    rec.lang = "es-MX";
    rec.continuous = true;
    rec.interimResults = true;
    let grabando = false;
    let base = "";

    rec.onresult = (ev) => {
      let final = "";
      let parcial = "";
      for (let i = 0; i < ev.results.length; i++) {
        const r = ev.results[i];
        if (r.isFinal) final += r[0].transcript + " ";
        else parcial += r[0].transcript;
      }
      texto.value = (base + final + parcial).replace(/\s+$/, "");
    };
    rec.onerror = (ev) => {
      if (ev.error === "not-allowed") mostrarError("Permite el uso del micrófono para dictar.");
      else if (ev.error !== "aborted" && ev.error !== "no-speech") mostrarError("No se pudo escuchar. Intenta de nuevo.");
      detener();
    };
    rec.onend = () => { if (grabando) detener(); };

    function iniciar() {
      mostrarError("");
      base = texto.value ? texto.value.replace(/\s+$/, "") + " " : "";
      grabando = true;
      btnMic.classList.add("grabando");
      btnMic.title = "Detener dictado";
      rec.start();
    }
    function detener() {
      grabando = false;
      btnMic.classList.remove("grabando");
      btnMic.title = "Dictar con la voz";
      try { rec.stop(); } catch {}
    }
    btnMic.addEventListener("click", () => (grabando ? detener() : iniciar()));
  }
})();
