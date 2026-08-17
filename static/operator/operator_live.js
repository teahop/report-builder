/* Live API bridge for the Phase 1 operator canvas. File upload is deferred. */
(function (root) {
  "use strict";

  const CASE_FIXTURE = {
    "001": "fixture_001.json",
    "005": "synthetic_history_case.json",
  };

  function fmtUsd(n) {
    if (typeof n !== "number" || Number.isNaN(n)) return "—";
    return "$" + n.toFixed(4);
  }

  function fmtMs(n) {
    if (typeof n !== "number" || Number.isNaN(n)) return "—";
    if (n >= 1000) return (n / 1000).toFixed(1) + " s";
    return Math.round(n) + " ms";
  }

  function nowStamp() {
    return new Date().toISOString().replace("T", " ").slice(0, 16);
  }

  async function getJson(path) {
    const res = await fetch(path);
    const text = await res.text();
    let data = null;
    try {
      data = JSON.parse(text);
    } catch (_) {
      /* not JSON */
    }
    if (!res.ok) {
      const detail =
        data && data.detail
          ? typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail)
          : text.slice(0, 800);
      throw new Error("HTTP " + res.status + ": " + detail);
    }
    return data;
  }

  async function postJson(path, body) {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const text = await res.text();
    let data = null;
    try {
      data = JSON.parse(text);
    } catch (_) {
      /* not JSON */
    }
    if (!res.ok) {
      const detail =
        data && data.detail
          ? typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail)
          : text.slice(0, 800);
      throw new Error("HTTP " + res.status + ": " + detail);
    }
    return data;
  }

  function defaultReferralContext() {
    return {
      evaluation_type: {
        context_id: "ctx_op_et",
        normalized_value: "private_psychoeducational_evaluation",
        capture_method: "clinician_entered",
        confirmation_state: "confirmed",
      },
      requested_by: [
        {
          context_id: "ctx_op_req",
          name: "Parent",
          role: "parent",
          capture_method: "clinician_entered",
          confirmation_state: "confirmed",
        },
      ],
      referral_trigger: {
        context_id: "ctx_op_trig",
        normalized_value:
          "clarify learning and attention concerns that persist despite classroom supports",
        capture_method: "clinician_entered",
        confirmation_state: "confirmed",
      },
      presenting_concerns: [
        {
          context_id: "ctx_op_pc1",
          normalized_value: "slow work completion and lost assignments",
          capture_method: "client_reported",
          confirmation_state: "confirmed",
        },
      ],
      client_goals: [
        {
          context_id: "ctx_op_goal",
          raw_text: "I want clear recommendations for how to help at home and school.",
          normalized_value: "obtain clear home and school recommendations",
          presentation_mode: "paraphrase",
          capture_method: "client_reported",
          confirmation_state: "confirmed",
        },
      ],
      suspected_disabilities: [
        {
          context_id: "ctx_op_sd1",
          category: "specific_learning_disability",
          capture_method: "clinician_confirmed",
          confirmation_state: "confirmed",
        },
        {
          context_id: "ctx_op_sd2",
          category: "other_health_impairment",
          capture_method: "clinician_confirmed",
          confirmation_state: "confirmed",
        },
      ],
    };
  }

  function filesFromSources(sources) {
    return (sources || []).map(function (s) {
      return [s.id, s.label, s.type, s.date, s.doc_class || "narrative"];
    });
  }

  function factsFromLedger(facts) {
    return (facts || []).map(function (f) {
      return [
        f.id,
        f.subject,
        f.predicate,
        f.qualifier,
        f.value,
        f.value_text,
        f.assertion,
        f.reporter,
        f.source_id,
        f.source_date,
        f.as_of_date,
        f.life_stage,
        f.temporality,
        f.confidence,
        f.valence,
      ];
    });
  }

  function conflictsFromApi(rows) {
    return (rows || []).map(function (d) {
      return {
        topic: d.topic,
        versions: (d.versions || []).map(function (v) {
          return [v.value || v.value_text || "", (v.source_id || "") + " · " + (v.source_date || "")];
        }),
      };
    });
  }

  function timelinesFromApi(rows) {
    return (rows || []).map(function (t) {
      const pred = t.predicate || t.topic || "";
      const entries = (t.entries || t.points || []).map(function (e) {
        return (e.value || "") + " (" + (e.as_of_date || e.date || "") + ")";
      });
      const seq =
        entries.length > 0
          ? entries.join(" → ")
          : t.sequence || t.summary || JSON.stringify(t);
      return [pred, seq];
    });
  }

  function gapFromReport(gap) {
    const sections = (gap && gap.sections) || [];
    const hist =
      sections.find(function (s) {
        return s.section === "history";
      }) || sections[0];
    if (!hist) {
      return {
        missing: [],
        freshness: [],
        stages: "—",
        sourceTypes: "—",
      };
    }
    const freshness = (hist.predicate_freshness || []).map(function (p) {
      const detail = p.latest_as_of_date
        ? "latest " + p.latest_as_of_date + (p.threshold_days != null ? " · threshold " + p.threshold_days + "d" : "")
        : p.state;
      return [p.state, p.predicate + (p.qualifier ? ":" + p.qualifier : ""), detail];
    });
    return {
      missing: hist.predicates_missing || [],
      freshness: freshness,
      stages: hist.available === false ? "section unavailable (no supporting facts)" : "—",
      sourceTypes: hist.available === false ? "no supporting document facts" : "—",
    };
  }

  function collectFromLive(live) {
    const items = [];
    const gap = live.gap;
    if (gap && gap.sections) {
      gap.sections.forEach(function (sec) {
        (sec.predicates_missing || []).forEach(function (name) {
          items.push([name, sec.section || ""]);
        });
      });
    }
    (live.predicates_for_review || []).forEach(function (name) {
      items.push(["proposed / unregistered predicate: " + name, "review"]);
    });
    return items;
  }

  function emptyDraft(endpoint) {
    return {
      status: "blocked",
      endpoint: endpoint,
      meta: [],
      fields: [],
      paragraphs: [],
      statements: [],
      checks: [],
      reviewItems: [],
      unanchored: [],
      footNote: "No live draft yet — run from the Draft tab.",
    };
  }

  function mapReferral(resp) {
    const blocked = !resp.ready_for_draft || !resp.section_populated;
    const rejected = resp.ready_for_draft && !resp.section_populated;
    const fields = []
      .concat(resp.missing_fields || [])
      .concat(resp.conflicting_fields || [])
      .map(function (f) {
        const cands = (f.candidate_values || f.candidates || []).join(" · ") || null;
        return [f.field, f.confirmation_state || (f.reason ? "not_yet_collected" : ""), f.reason || "", cands];
      });
    const paragraphs = (resp.paragraphs || []).map(function (text) {
      return { label: null, text: text };
    });
    if (!paragraphs.length && resp.prose) {
      paragraphs.push({ label: null, text: resp.prose });
    }
    const statements = (resp.statements || []).map(function (s) {
      return [s.quote || s.claim || "", s.normalized_claim || "", s.support_ids || s.fact_ids || []];
    });
    return {
      status: blocked ? "blocked" : rejected ? "rejected" : "accepted",
      endpoint: "POST /draft/referral",
      meta: [
        ["tokens", String(resp.tokens_used ?? "—")],
        ["latency", fmtMs(resp.latency_ms)],
        ["cost", fmtUsd(resp.cost_usd)],
        ["model", resp.model || "—"],
        ["prompt", (resp.prompt_sha256 || "").slice(0, 8) || "—"],
      ],
      fields: fields,
      paragraphs: paragraphs,
      statements: statements,
      checks: [],
      reviewItems: ((resp.review && resp.review.items) || []).map(function (i) {
        return [i.kind, i.summary];
      }),
      unanchored: [],
      footNote: blocked
        ? "ready_for_draft: false — typed completion; nothing was sent to a model."
        : "Live referral draft. Phase 1 uses a built-in synthetic ReferralContext (form comes later).",
    };
  }

  function mapHistory(resp) {
    const populated = !!resp.section_populated;
    const sections = (resp.package && resp.package.sections) || [];
    const paragraphs = [];
    const statements = [];
    sections.forEach(function (sec) {
      if (!sec.section_populated) return;
      const blocks = sec.blocks || [];
      if (blocks.length) {
        blocks.forEach(function (b) {
          const prose = (b.draft_block && b.draft_block.prose) || "";
          if (prose) paragraphs.push({ label: b.display_label || sec.display_label, text: prose });
          ((b.draft_block && b.draft_block.statements) || []).forEach(function (s) {
            statements.push([s.quote || "", s.normalized_claim || "", s.fact_ids || []]);
          });
        });
      } else if (sec.draft_output && sec.draft_output.prose) {
        paragraphs.push({ label: sec.display_label, text: sec.draft_output.prose });
      }
    });
    if (!paragraphs.length && resp.rendered_prose) {
      paragraphs.push({ label: null, text: resp.rendered_prose });
    }
    const vg = resp.voice_gate || {};
    const vgChecks = (vg.checks || []).map(function (c) {
      return [c.id || c.rule_id || "voice", c.result === "fail" ? "fail" : c.result || "pass", c.summary || ""];
    });
    const reviewItems = ((resp.review && resp.review.items) || []).map(function (i) {
      return [i.kind, i.summary];
    });
    const failing = vgChecks.some(function (c) {
      return c[1] === "fail";
    }) || reviewItems.some(function (i) {
      return i[0] === "entailment_failure" || i[0] === "visible_fact_id";
    });
    return {
      status: !populated ? "blocked" : failing ? "rejected" : "accepted",
      endpoint: "POST /draft/history",
      meta: [
        ["tokens", String(resp.tokens_used ?? "—")],
        ["latency", fmtMs(resp.latency_ms)],
        ["cost", fmtUsd(resp.cost_usd)],
        ["model", resp.model || "—"],
        ["prompt", (resp.prompt_hash || "").slice(0, 8) || "—"],
        ["voice", (resp.voice_store_sha || "").slice(0, 8) || "—"],
      ],
      fields: [],
      paragraphs: paragraphs,
      statements: statements,
      checks: vgChecks,
      reviewItems: reviewItems,
      unanchored: [],
      footNote: populated
        ? "Live History package. Prose view is unlabeled; Verify re-injects evidence ids."
        : resp.empty_reason || "History section not populated.",
    };
  }

  function runRow(endpoint, caseId, resp, outcome, note) {
    const stages = resp.tokens_by_stage
      ? Object.keys(resp.tokens_by_stage)
          .map(function (k) {
            return k + " " + resp.tokens_by_stage[k];
          })
          .join(" · ")
      : "—";
    return [
      nowStamp(),
      endpoint,
      caseId,
      outcome,
      note,
      resp.model || "—",
      String(resp.tokens_used ?? "—"),
      stages,
      fmtMs(resp.latency_ms),
      fmtUsd(resp.cost_usd),
      (resp.prompt_sha256 || resp.prompt_hash || "").slice(0, 8) || "—",
      resp.langfuse_url ? "trace ↗" : "—",
    ];
  }

  function applyPacket(live, packet) {
    live.child = packet.child;
    live.sources = packet.sources || [];
    live.files = filesFromSources(live.sources);
    live.statusLine =
      "Fixture packet loaded — " + live.files.length + " sources. Extract or load cached ledger next.";
    return live;
  }

  function applyLedger(live, payload, statusLine) {
    live.ledger = payload.ledger;
    live.child = (payload.ledger && payload.ledger.child) || live.child;
    live.conflicts = payload.conflicts || [];
    live.variance = payload.variance || [];
    live.timelines = payload.timelines || [];
    live.gap = payload.gap_report || live.gap;
    live.predicates_for_review = payload.predicates_for_review || [];
    live.subjects_for_review = payload.subjects_for_review || [];
    if (payload.ledger && payload.ledger.sources) {
      live.files = filesFromSources(payload.ledger.sources);
    }
    if (!live.drafts) live.drafts = {};
    if (!live.drafts.referral) live.drafts.referral = emptyDraft("POST /draft/referral");
    if (!live.drafts.history) live.drafts.history = emptyDraft("POST /draft/history");
    live.statusLine = statusLine;
    return live;
  }

  function viewFromLive(base, live) {
    const out = Object.assign({}, base);
    if (live.child) {
      out.name = live.child.name || out.name;
      out.dob = live.child.dob || out.dob;
      out.evalDate = live.child.evaluation_date || out.evalDate;
    }
    if (live.files && live.files.length) out.files = live.files;
    if (live.ledger && live.ledger.facts) {
      out.facts = factsFromLedger(live.ledger.facts);
      const n = live.ledger.facts.length;
      const ns = (live.ledger.sources || []).length;
      out.ledgerMeta =
        "live ledger v" +
        (live.ledger.ledger_version || "?") +
        " · " +
        ns +
        " sources · " +
        n +
        " facts";
      out.drafts = Object.assign(
        {
          referral: emptyDraft("POST /draft/referral"),
          history: emptyDraft("POST /draft/history"),
        },
        live.drafts || {}
      );
    }
    if (live.conflicts) out.conflicts = conflictsFromApi(live.conflicts);
    if (live.variance) out.variance = conflictsFromApi(live.variance);
    if (live.timelines) out.timelines = timelinesFromApi(live.timelines);
    if (live.gap) out.gap = gapFromReport(live.gap);
    const collected = collectFromLive(live);
    if (collected.length) out.collectItems = collected;
    if (live.predicates_for_review) {
      out.heldPredicates = live.predicates_for_review.map(function (name) {
        return [name, "unregistered / proposed — awaiting vocabulary ruling"];
      });
    }
    if (live.runs && live.runs.length) out.runs = live.runs;
    return out;
  }

  async function loadPacket(caseId) {
    const name = CASE_FIXTURE[caseId];
    if (!name) throw new Error("No fixture mapped for case " + caseId);
    return getJson("/fixtures/" + name);
  }

  async function loadCached001() {
    const ledger = await getJson("/fixtures/cached_ledger_001");
    const conf = await postJson("/conflicts", { confirm_synthetic: true, ledger: ledger });
    return {
      ledger: ledger,
      conflicts: conf.conflicts || [],
      variance: conf.variance || [],
      timelines: conf.timelines || [],
      predicates_for_review: conf.predicates_for_review || [],
      subjects_for_review: conf.subjects_for_review || [],
    };
  }

  async function extractLedger(child, sources) {
    const extract = await postJson("/extract", {
      confirm_synthetic: true,
      child: child,
      sources: sources,
      model: "gpt-4o-mini",
    });
    const conf = await postJson("/conflicts", {
      confirm_synthetic: true,
      ledger: extract.ledger,
    });
    return {
      ledger: extract.ledger,
      gap_report: extract.gap_report,
      tokens_used: extract.tokens_used,
      cost_usd: extract.cost_usd,
      latency_ms: extract.latency_ms,
      model: extract.model,
      tokens_by_stage: extract.tokens_by_source,
      conflicts: conf.conflicts || [],
      variance: conf.variance || [],
      timelines: conf.timelines || [],
      predicates_for_review: extract.predicates_for_review || [],
      subjects_for_review: extract.subjects_for_review || [],
    };
  }

  async function draftReferral(ledger) {
    return postJson("/draft/referral", {
      confirm_synthetic: true,
      ledger: ledger,
      context: defaultReferralContext(),
      eval_fixture_id: "operator_ui",
    });
  }

  async function draftHistory(ledger, conflicts, variance) {
    return postJson("/draft/history", {
      confirm_synthetic: true,
      ledger: ledger,
      conflicts: conflicts || [],
      variance: variance || [],
      model: "gpt-4o-mini",
      entailment_model: "gpt-4o-mini",
    });
  }

  root.OperatorLive = {
    CASE_FIXTURE: CASE_FIXTURE,
    loadPacket: loadPacket,
    loadCached001: loadCached001,
    extractLedger: extractLedger,
    draftReferral: draftReferral,
    draftHistory: draftHistory,
    mapReferral: mapReferral,
    mapHistory: mapHistory,
    runRow: runRow,
    applyPacket: applyPacket,
    applyLedger: applyLedger,
    viewFromLive: viewFromLive,
    filesFromSources: filesFromSources,
    emptyDraft: emptyDraft,
  };
})(window);
