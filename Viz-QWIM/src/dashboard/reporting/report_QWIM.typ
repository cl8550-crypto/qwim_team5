// ============================================================================
// QWIM Portfolio Analysis Report  Typst Template
//
// Data sources (all relative to this file's directory):
//   data_clients.json             client info (personal_info, assets, goals,
//                                 income) + advisor_info
//   data_results.json             all analysis inputs and outputs per subtab
//   report_config.json            report metadata, section enable flags,
//                                 include_partner flag
//
// Legacy files (kept for backward compatibility):
//   client_info.json, report_metadata.json, inputs_json/, outputs_json/
//
// All data is read via Typst's native json() function.
// ============================================================================

#import "utils_reporting.typ": *
#import "utils_colors.typ": *
#import "utils_fonts.typ": *
#import "utils_table.typ": *
#import "utils_formatting.typ": *

// ============================================================================
// 0.  LOAD DATA
// ============================================================================

#let clients = json("data_clients.json")
#let results = json("data_results.json")
#let config  = json("report_config.json")

// Convenience aliases that preserve old variable names so section bodies need
// no changes beyond the defensive-guard block below.
#let meta = (
  report_date:  config.at("report_date",  default: "N/A"),
  report_version: "1.0",
  generated_by: "QWIM Analytics Platform",
)
#let client = clients

#let in_pa  = results.at("Portfolio_Analysis_Inputs",              default: (:))
#let out_pa = results.at("Portfolio_Analysis_Outputs",             default: (:))

#let in_pc  = results.at("Portfolio_Comparison_Inputs",            default: (:))
#let out_pc = results.at("Portfolio_Comparison_Outputs",           default: (:))

#let in_wa  = results.at("Weights_Analysis_Inputs",                default: (:))
#let out_wa = results.at("Weights_Analysis_Outputs",               default: (:))

#let in_sk  = results.at("Portfolio_Optimization_Skfolio_Inputs",  default: (:))
#let out_sk = results.at("Portfolio_Optimization_Skfolio_Outputs", default: (:))

#let in_op  = results.at("Portfolio_Optimization_OptimalPortfolios_Inputs",  default: (:))
#let out_op = results.at("Portfolio_Optimization_OptimalPortfolios_Outputs", default: (:))

#let in_sim  = results.at("Portfolio_Simulation_Inputs",           default: (:))
#let out_sim = results.at("Portfolio_Simulation_Outputs",          default: (:))

#let in_gp  = results.at("Goal_Parity_Inputs",                     default: (:))
#let out_gp = results.at("Goal_Parity_Outputs",                    default: (:))

// ---- Defensive helpers ----------------------------------------------------
// safe_merge: merge *actual* (from JSON) into *defaults* — avoids the
// "cannot spread dictionary into array" error that (..) spreads can trigger.
#let safe_merge(defaults, actual) = {
  if type(actual) == dictionary { defaults + actual }
  else { defaults }
}

// safe_array: guarantee a value is an array before iterating.
#let safe_array(val) = {
  if type(val) == array { val }
  else { () }
}

// ---- Defensive defaults for nested structures ----------------------------
// Uses  dict + dict  (the Typst merge operator) instead of  (..dict, ..dict)
// to prevent "cannot spread dictionary into array" compilation errors.

#let _empty_metric = (portfolio: 0.0, benchmark: 0.0, difference: 0.0)

// Guard out_pc.metrics
#let out_pc = {
  let _m = if type(out_pc) == dictionary { out_pc.at("metrics", default: (:)) } else { (:) }
  let _m = if type(_m) == dictionary { _m } else { (:) }
  let guarded_metrics = (
    total_return:      safe_merge(_empty_metric, _m.at("total_return",      default: (:))),
    annualized_return: safe_merge(_empty_metric, _m.at("annualized_return", default: (:))),
    volatility:        safe_merge(_empty_metric, _m.at("volatility",        default: (:))),
    max_drawdown:      safe_merge(_empty_metric, _m.at("max_drawdown",      default: (:))),
    sharpe_ratio:      safe_merge(_empty_metric, _m.at("sharpe_ratio",      default: (:))),
    correlation:       _m.at("correlation",       default: 0.0),
    tracking_error:    _m.at("tracking_error",    default: 0.0),
    information_ratio: _m.at("information_ratio", default: 0.0),
  )
  if type(out_pc) == dictionary { out_pc + (metrics: guarded_metrics) }
  else { (metrics: guarded_metrics) }
}

// Guard out_sim.summary_statistics
#let out_sim = {
  let _ss = if type(out_sim) == dictionary { out_sim.at("summary_statistics", default: (:)) } else { (:) }
  let _ss = if type(_ss) == dictionary { _ss } else { (:) }
  let guarded_ss = (
    num_scenarios:          _ss.at("num_scenarios",          default: 0),
    horizon_days:           _ss.at("horizon_days",           default: 0),
    initial_value:          _ss.at("initial_value",          default: 100.0),
    mean_terminal_value:    _ss.at("mean_terminal_value",    default: 0.0),
    median_terminal_value:  _ss.at("median_terminal_value",  default: 0.0),
    std_dev_terminal_value: _ss.at("std_dev_terminal_value", default: 0.0),
    percentile_5:           _ss.at("percentile_5",           default: 0.0),
    percentile_25:          _ss.at("percentile_25",          default: 0.0),
    percentile_75:          _ss.at("percentile_75",          default: 0.0),
    percentile_95:          _ss.at("percentile_95",          default: 0.0),
    min_terminal_value:     _ss.at("min_terminal_value",     default: 0.0),
    max_terminal_value:     _ss.at("max_terminal_value",     default: 0.0),
    probability_of_loss:    _ss.at("probability_of_loss",    default: 0.0),
  )
  if type(out_sim) == dictionary { out_sim + (summary_statistics: guarded_ss) }
  else { (summary_statistics: guarded_ss) }
}

// Guard out_gp.goal_powers / rebalancing
#let _default_goal_powers = (Liquidity: 0.25, Income: 0.25, Preservation: 0.25, Growth: 0.25)
#let _default_rebalancing = (traded: false, num_trades: 0, turnover: 0.0,
  goal_powers_before: _default_goal_powers, goal_powers_after: _default_goal_powers)
#let out_gp = {
  let _gpow = if type(out_gp) == dictionary { out_gp.at("goal_powers", default: (:)) } else { (:) }
  let _gpow = if type(_gpow) == dictionary { _gpow } else { (:) }
  let _reb  = if type(out_gp) == dictionary { out_gp.at("rebalancing", default: (:)) } else { (:) }
  let _reb  = if type(_reb) == dictionary { _reb } else { (:) }
  let guarded_goal_powers = safe_merge(_default_goal_powers, _gpow)
  let guarded_rebalancing = (
    traded: _reb.at("traded", default: false),
    num_trades: _reb.at("num_trades", default: 0),
    turnover: _reb.at("turnover", default: 0.0),
    goal_powers_before: safe_merge(_default_goal_powers, _reb.at("goal_powers_before", default: (:))),
    goal_powers_after: safe_merge(_default_goal_powers, _reb.at("goal_powers_after", default: (:))),
  )
  let base = if type(out_gp) == dictionary { out_gp } else { (:) }
  base + (
    mode: base.at("mode", default: "balanced"),
    expected_return: base.at("expected_return", default: 0.0),
    solver_success: base.at("solver_success", default: true),
    goal_powers: guarded_goal_powers,
    scarce_goals: safe_array(base.at("scarce_goals", default: ())),
    top_weights: safe_array(base.at("top_weights", default: ())),
    rebalancing: guarded_rebalancing,
  )
}

// Guard out_sk.performance_summary
#let _default_sk_method = (label: "N/A", annualized_return: 0.0, volatility: 0.0, sharpe_ratio: 0.0)
#let out_sk = {
  let _ps = if type(out_sk) == dictionary { out_sk.at("performance_summary", default: (:)) } else { (:) }
  let _ps = if type(_ps) == dictionary { _ps } else { (:) }
  let guarded_ps = (
    method1: safe_merge(_default_sk_method, _ps.at("method1", default: (:))),
    method2: safe_merge(_default_sk_method, _ps.at("method2", default: (:))),
  )
  if type(out_sk) == dictionary { out_sk + (performance_summary: guarded_ps) }
  else { (performance_summary: guarded_ps) }
}

// Guard out_op.performance_summary
#let _default_op_method = (label: "N/A", annualized_return: 0.0, volatility: 0.0, sharpe_ratio: 0.0)
#let out_op = {
  let _ps = if type(out_op) == dictionary { out_op.at("performance_summary", default: (:)) } else { (:) }
  let _ps = if type(_ps) == dictionary { _ps } else { (:) }
  let guarded_ps = (
    method1: safe_merge(_default_op_method, _ps.at("method1", default: (:))),
    method2: safe_merge(_default_op_method, _ps.at("method2", default: (:))),
  )
  if type(out_op) == dictionary { out_op + (performance_summary: guarded_ps) }
  else { (performance_summary: guarded_ps) }
}

// Guard client sub-structures
#let _default_person = (name: "N/A", age_current: "N/A", age_retirement: "N/A",
  age_income_starting: "N/A", status_marital: "N/A", gender: "N/A",
  tolerance_risk: "N/A", state: "N/A", code_zip: "N/A")
#let _default_money = (taxable: 0.0, tax_deferred: 0.0, tax_free: 0.0, total: 0.0)
#let _default_goals = (essential: 0.0, important: 0.0, aspirational: 0.0, total: 0.0)
#let _default_income = (social_security: 0.0, pension: 0.0, annuity_existing: 0.0, other: 0.0, total: 0.0)

#let client = {
  let _pi = if type(client) == dictionary { client.at("personal_info", default: (:)) } else { (:) }
  let _a  = if type(client) == dictionary { client.at("assets",        default: (:)) } else { (:) }
  let _g  = if type(client) == dictionary { client.at("goals",         default: (:)) } else { (:) }
  let _i  = if type(client) == dictionary { client.at("income",        default: (:)) } else { (:) }
  let _pi = if type(_pi) == dictionary { _pi } else { (:) }
  let _a  = if type(_a)  == dictionary { _a  } else { (:) }
  let _g  = if type(_g)  == dictionary { _g  } else { (:) }
  let _i  = if type(_i)  == dictionary { _i  } else { (:) }
  let base = if type(client) == dictionary { client } else { (:) }
  base + (
    personal_info: (
      primary: safe_merge(_default_person, _pi.at("primary", default: (:))),
      partner: safe_merge(_default_person, _pi.at("partner", default: (:))),
    ),
    assets: (
      primary:  safe_merge(_default_money, _a.at("primary",  default: (:))),
      partner:  safe_merge(_default_money, _a.at("partner",  default: (:))),
      combined: safe_merge(_default_money, _a.at("combined", default: (:))),
    ),
    goals: (
      primary:  safe_merge(_default_goals, _g.at("primary",  default: (:))),
      partner:  safe_merge(_default_goals, _g.at("partner",  default: (:))),
      combined: safe_merge(_default_goals, _g.at("combined", default: (:))),
    ),
    income: (
      primary:  safe_merge(_default_income, _i.at("primary",  default: (:))),
      partner:  safe_merge(_default_income, _i.at("partner",  default: (:))),
      combined: safe_merge(_default_income, _i.at("combined", default: (:))),
    ),
  )
}

// ============================================================================
// 1.  HELPER FUNCTIONS
// ============================================================================

// functions moved to file utils_reporting.typ

// ============================================================================
// 2.  DOCUMENT SETTINGS
// ============================================================================

#set text(lang: "en", font: "Arial", size: 11pt)
#set page(
  paper: "a4",
  margin: (x: 2.4cm, y: 2.2cm),
  header: context {
    if counter(page).get().first() > 1 [
      #set text(size: 9pt, fill: rgb("#6b7280"))
      #grid(
        columns: (1fr, 1fr),
        align(left)[QWIM Portfolio Analysis Report],
        align(right)[#meta.report_date],
      )
      #line(length: 100%, stroke: 0.5pt + rgb("#d1d5db"))
    ]
  },
  footer: context {
    if counter(page).get().first() > 1 [
      #line(length: 100%, stroke: 0.5pt + rgb("#d1d5db"))
      #set text(size: 9pt, fill: rgb("#6b7280"))
      #grid(
        columns: (1fr, 1fr),
        align(left)[#meta.generated_by],
        align(right)[Page #counter(page).display() of #counter(page).final().first()],
      )
    ]
  },
)

#set par(justify: true, leading: 0.75em)
#set heading(numbering: "1.1")

// ============================================================================
// 3.  STYLING HELPERS
// ============================================================================

// Coloured section rule
#let section_rule(col: rgb("#1d4ed8")) = {
  v(0.4em)
  line(length: 100%, stroke: 1.5pt + col)
  v(0.15em)
}

// Highlight box  light blue
#let info_box(content) = block(
  fill: rgb("#eff6ff"),
  inset: (x: 1em, y: 0.75em),
  radius: 5pt,
  stroke: 0.5pt + rgb("#bfdbfe"),
  width: 100%,
)[#content]

// Warning / note box  amber
#let note_box(content) = block(
  fill: rgb("#fffbeb"),
  inset: (x: 1em, y: 0.75em),
  radius: 5pt,
  stroke: 0.5pt + rgb("#fcd34d"),
  width: 100%,
)[#content]

// KPI tile  compact metric card
#let kpi_card(label, value, sub: none, accent: rgb("#1d4ed8")) = block(
  fill: rgb("#f8fafc"),
  inset: (x: 0.9em, y: 0.7em),
  radius: 5pt,
  stroke: 0.5pt + rgb("#e2e8f0"),
)[
  #set text(size: 9pt, fill: rgb("#6b7280"))
  #label \
  #set text(size: 14pt, weight: "bold", fill: accent)
  #value
  #if sub != none [
    #set text(size: 8pt, fill: rgb("#94a3b8"))
    \ #sub
  ]
]

// Standard styled table  blue header, alternating rows
#let styled_table(..args) = figure(
  table(
    stroke: (x: none, y: 0.5pt + rgb("#e5e7eb")),
    fill: (_, y) =>
      if y == 0       { rgb("#1d4ed8") }
      else if calc.odd(y) { rgb("#f8fafc") },
    inset: (x: 0.7em, y: 0.55em),
    ..args,
  ),
  kind: table,
)

// Teal-header table variant for comparison sections
#let styled_table_teal(..args) = figure(
  table(
    stroke: (x: none, y: 0.5pt + rgb("#e5e7eb")),
    fill: (_, y) =>
      if y == 0       { rgb("#0f766e") }
      else if calc.odd(y) { rgb("#f0fdf4") },
    inset: (x: 0.7em, y: 0.55em),
    ..args,
  ),
  kind: table,
)

// ============================================================================
// 4.  TITLE PAGE
// ============================================================================

#page(margin: (x: 2.4cm, y: 2.8cm), header: none, footer: none)[
  #v(1.5cm)

  // Brand bar
  #block(
    fill: rgb("#1d4ed8"),
    inset: (x: 1.4em, y: 1.12em),
    radius: 6pt,
    width: 100%,
  )[
    #set text(fill: white, weight: "bold")
    #stack(
      spacing: 0.24em,
      text(size: 21pt)[QWIM Analytics],
      text(size: 10.5pt)[Quantitative Wealth & Investment Management],
    )
  ]

  #v(1.8cm)

  // Report title
  #align(center)[
    #text(size: 28pt, weight: "bold", fill: rgb("#1e293b"))[Portfolio Analysis Report]
    #v(0.4cm)
    #text(size: 16pt, fill: rgb("#475569"))[Comprehensive Investor & Portfolio Review]
  ]

  #v(1.4cm)

  // Metadata strip
  #block(
    fill: rgb("#f1f5f9"),
    inset: (x: 1.4em, y: 1em),
    radius: 6pt,
    stroke: 0.5pt + rgb("#cbd5e1"),
  )[
    #grid(
      columns: (1fr, 1fr),
      row-gutter: 0.6em,
      [*Report Date*],     [#meta.report_date],
      [*Analysis Period*], [#field(out_pc, "time_period") -- #field(out_pc, "start_date") to #field(out_pc, "end_date")],
      [*Version*],         [#meta.report_version],
      [*Prepared by*],     [#meta.generated_by],
    )
  ]

  #v(1.8cm)

  // Investor summary cards
  #grid(
    columns: (1fr, 0.06fr, 1fr),
    block(
      fill: white,
      inset: 1.1em,
      radius: 6pt,
      stroke: 0.8pt + rgb("#1d4ed8"),
    )[
      #set text(size: 10pt)
      #text(weight: "bold", fill: rgb("#1d4ed8"), size: 11pt)[Primary Investor] \
      #v(0.3em)
      *Name:* #field(client.personal_info.primary, "name") \
      *Age:* #field(client.personal_info.primary, "age_current") \
      *Retire At:* #field(client.personal_info.primary, "age_retirement") \
      *Risk:* #risk_badge(field(client.personal_info.primary, "tolerance_risk")) \
      *State:* #field(client.personal_info.primary, "state")
    ],
    [],
    block(
      fill: white,
      inset: 1.1em,
      radius: 6pt,
      stroke: 0.8pt + rgb("#0f766e"),
    )[
      #set text(size: 10pt)
      #text(weight: "bold", fill: rgb("#0f766e"), size: 11pt)[Partner Investor] \
      #v(0.3em)
      *Name:* #field(client.personal_info.partner, "name") \
      *Age:* #field(client.personal_info.partner, "age_current") \
      *Retire At:* #field(client.personal_info.partner, "age_retirement") \
      *Risk:* #risk_badge(field(client.personal_info.partner, "tolerance_risk")) \
      *State:* #field(client.personal_info.partner, "state")
    ],
  )

  #v(1.6cm)
]

// ============================================================================
// 4.5  ABSTRACT PAGE
// ============================================================================

#page(margin: (x: 2.4cm, y: 2.8cm), header: none, footer: none)[
  #v(2.0cm)

  #align(center)[
    #text(size: 24pt, weight: "bold", fill: rgb("#1e293b"))[Abstract]
  ]

  #v(1.0cm)

  #block(
    fill: rgb("#f8fafc"),
    inset: (x: 1.4em, y: 1.1em),
    radius: 6pt,
    stroke: 0.5pt + rgb("#e2e8f0"),
  )[
    #set text(size: 10.5pt, fill: rgb("#374151"))
    This report provides a comprehensive analysis of portfolio allocation and investor
    information from the QWIM Analytics platform. The analysis covers personal demographics,
    multi-category asset allocation by tax treatment, financial goals prioritisation,
    projected retirement income planning, portfolio weights analysis, performance comparison
    against benchmark data, skfolio optimisation results, and Monte Carlo simulation outcomes.
    All data reflects the current state of the QWIM Analytics dashboard as of #meta.report_date.
  ]
]

// ============================================================================
// 5.  TABLE OF CONTENTS
// ============================================================================

#page(margin: (x: 2.4cm, y: 2.2cm), header: none, footer: none)[
  #outline(
    title: text(size: 18pt, weight: "bold")[Table of Contents],
    indent: auto,
    depth: 3,
  )
]

// ============================================================================
// 6.  MAIN CONTENT  reset page counter
// ============================================================================

#counter(page).update(1)

// ============================================================================
// SECTION 1  INVESTOR INFORMATION
// ============================================================================

= Investor Information

#section_rule()

This section documents the complete demographic and financial profile of both investors,
underpinning all subsequent portfolio analysis and planning recommendations.

// ---------------------------------------------------------------------------
== Personal Information

#info_box[
  The demographics below are sourced from the *Clients -- Personal Info* subtab and
  drive all age-sensitive projections including retirement timeline, income-starting age,
  and longevity-adjusted withdrawal strategies.
]

#v(0.5em)

=== #field(client.personal_info.primary, "name") -- Primary Investor

#grid(
  columns: (1fr, 1fr),
  gutter: 1.2em,
  [
    #styled_table(
      columns: (auto, 1fr),
      table.header(
        text(fill: white, weight: "bold")[Attribute],
        text(fill: white, weight: "bold")[Value],
      ),
      [Current Age],       [#field(client.personal_info.primary, "age_current") years],
      [Retirement Age],    [#field(client.personal_info.primary, "age_retirement") years],
      [Income Start Age],  [#field(client.personal_info.primary, "age_income_starting") years],
      [Gender],            [#field(client.personal_info.primary, "gender")],
      [Marital Status],    [#field(client.personal_info.primary, "status_marital")],
    )
  ],
  [
    #styled_table(
      columns: (auto, 1fr),
      table.header(
        text(fill: white, weight: "bold")[Attribute],
        text(fill: white, weight: "bold")[Value],
      ),
      [Risk Tolerance],    [#risk_badge(field(client.personal_info.primary, "tolerance_risk"))],
      [State],             [#field(client.personal_info.primary, "state")],
      [ZIP Code],          [#field(client.personal_info.primary, "code_zip")],
      [Planning Horizon],  [#{
        let _age = field(client.personal_info.primary, "age_current")
        if _age == "N/A" { "N/A" } else { str(95 - safe_int(_age)) + " yrs" }
      }],
    )
  ],
)

#v(0.8em)

=== #field(client.personal_info.partner, "name") -- Partner Investor

#grid(
  columns: (1fr, 1fr),
  gutter: 1.2em,
  [
    #styled_table(
      columns: (auto, 1fr),
      table.header(
        text(fill: white, weight: "bold")[Attribute],
        text(fill: white, weight: "bold")[Value],
      ),
      [Current Age],       [#field(client.personal_info.partner, "age_current") years],
      [Retirement Age],    [#field(client.personal_info.partner, "age_retirement") years],
      [Income Start Age],  [#field(client.personal_info.partner, "age_income_starting") years],
      [Gender],            [#field(client.personal_info.partner, "gender")],
      [Marital Status],    [#field(client.personal_info.partner, "status_marital")],
    )
  ],
  [
    #styled_table(
      columns: (auto, 1fr),
      table.header(
        text(fill: white, weight: "bold")[Attribute],
        text(fill: white, weight: "bold")[Value],
      ),
      [Risk Tolerance],    [#risk_badge(field(client.personal_info.partner, "tolerance_risk"))],
      [State],             [#field(client.personal_info.partner, "state")],
      [ZIP Code],          [#field(client.personal_info.partner, "code_zip")],
      [Planning Horizon],  [#{
        let _age = field(client.personal_info.partner, "age_current")
        if _age == "N/A" { "N/A" } else { str(95 - safe_int(_age)) + " yrs" }
      }],
    )
  ],
)

// ---------------------------------------------------------------------------
== Asset Allocation

#info_box[
  Assets are categorised by tax treatment -- *taxable*, *tax-deferred*, and *tax-free* --
  to enable optimised withdrawal sequencing and after-tax return maximisation.
  Tax-deferred assets are subject to RMDs beginning at age 73 (SECURE 2.0).
]

#v(0.5em)

#styled_table(
  columns: (2fr, 1.4fr, 1.4fr, 1.4fr, 1.4fr),
  table.header(
    text(fill: white, weight: "bold")[Asset Category],
    text(fill: white, weight: "bold")[Primary],
    text(fill: white, weight: "bold")[Partner],
    text(fill: white, weight: "bold")[Combined],
    text(fill: white, weight: "bold")[% of Total],
  ),
  [Taxable Assets],
    [#fmt_usd(client.assets.primary.taxable)],
    [#fmt_usd(client.assets.partner.taxable)],
    [#fmt_usd(client.assets.combined.taxable)],
    [#fmt_pct(safe_div(client.assets.combined.taxable, client.assets.combined.total))],
  [Tax-Deferred (401k / IRA)],
    [#fmt_usd(client.assets.primary.tax_deferred)],
    [#fmt_usd(client.assets.partner.tax_deferred)],
    [#fmt_usd(client.assets.combined.tax_deferred)],
    [#fmt_pct(safe_div(client.assets.combined.tax_deferred, client.assets.combined.total))],
  [Tax-Free (Roth)],
    [#fmt_usd(client.assets.primary.tax_free)],
    [#fmt_usd(client.assets.partner.tax_free)],
    [#fmt_usd(client.assets.combined.tax_free)],
    [#fmt_pct(safe_div(client.assets.combined.tax_free, client.assets.combined.total))],
  table.hline(stroke: 1pt + rgb("#1d4ed8")),
  [*Total Assets*],
    [*#fmt_usd(client.assets.primary.total)*],
    [*#fmt_usd(client.assets.partner.total)*],
    [*#fmt_usd(client.assets.combined.total)*],
    [*100.00 %*],
)

#v(0.6em)

#grid(
  columns: (1fr, 1fr, 1fr, 1fr),
  gutter: 0.8em,
  kpi_card("Total Combined Assets",    fmt_usd(client.assets.combined.total),     sub: "All categories"),
  kpi_card("Primary Investor",         fmt_usd(client.assets.primary.total),      sub: "Individual total"),
  kpi_card("Partner Investor",         fmt_usd(client.assets.partner.total),      sub: "Individual total"),
  kpi_card("Tax-Deferred Share",
    fmt_pct(safe_div(client.assets.combined.tax_deferred, client.assets.combined.total)),
    sub: "401k / IRA / pension"),
)

#note_box[
  *Tax-efficiency note:* A high proportion of assets in tax-deferred accounts may benefit
  from Roth conversion strategies before RMDs begin at age 73 (SECURE 2.0 Act).
  Consult a qualified tax advisor before implementing conversion strategies.
]

// ---------------------------------------------------------------------------
== Financial Goals

#info_box[
  Goals are classified into three tiers: *Essential* (non-negotiable baseline needs),
  *Important* (quality-of-life enhancing), and *Aspirational* (optimal legacy/lifestyle
  outcomes). Coverage ratio compares current assets to total funding requirement.
]

#v(0.5em)

#styled_table(
  columns: (2fr, 1.4fr, 1.4fr, 1.4fr),
  table.header(
    text(fill: white, weight: "bold")[Priority Tier],
    text(fill: white, weight: "bold")[Primary],
    text(fill: white, weight: "bold")[Partner],
    text(fill: white, weight: "bold")[Combined],
  ),
  [Essential Goals],    [#fmt_usd(client.goals.primary.essential)],    [#fmt_usd(client.goals.partner.essential)],    [#fmt_usd(client.goals.combined.essential)],
  [Important Goals],    [#fmt_usd(client.goals.primary.important)],    [#fmt_usd(client.goals.partner.important)],    [#fmt_usd(client.goals.combined.important)],
  [Aspirational Goals], [#fmt_usd(client.goals.primary.aspirational)], [#fmt_usd(client.goals.partner.aspirational)], [#fmt_usd(client.goals.combined.aspirational)],
  table.hline(stroke: 1pt + rgb("#1d4ed8")),
  [*Total Funding Need*],
    [*#fmt_usd(client.goals.primary.total)*],
    [*#fmt_usd(client.goals.partner.total)*],
    [*#fmt_usd(client.goals.combined.total)*],
)

#v(0.5em)

#grid(
  columns: (1fr, 1fr, 1fr, 1fr),
  gutter: 0.8em,
  kpi_card("Total Funding Need",   fmt_usd(client.goals.combined.total),     sub: "All tiers combined"),
  kpi_card("Essential Floor",      fmt_usd(client.goals.combined.essential), sub: "Must-fund minimum"),
  kpi_card("Wealth Coverage",
    fmt_pct(safe_div(client.assets.combined.total, client.goals.combined.total)),
    sub: "Assets / Goals"),
  block(
    fill: rgb("#f8fafc"),
    inset: (x: 0.9em, y: 0.7em),
    radius: 5pt,
    stroke: 0.5pt + rgb("#e2e8f0"),
  )[
    #set text(size: 9pt, fill: rgb("#6b7280"))
    Funding Status \
    #v(0.15em)
    #sufficiency_badge(safe_div(client.assets.combined.total, client.goals.combined.total))
    #v(0.1em)
    #set text(size: 8pt, fill: rgb("#94a3b8"))
    vs total goal need
  ],
)

// ---------------------------------------------------------------------------
== Projected Retirement Income

#info_box[
  Projected *annual* income at income-start age. Social Security and pension values
  are based on current benefit statements. All values are nominal (not inflation-adjusted).
  Guaranteed income = Social Security + Pension (not subject to market risk).
]

#v(0.5em)

#styled_table(
  columns: (2fr, 1.4fr, 1.4fr, 1.4fr),
  table.header(
    text(fill: white, weight: "bold")[Income Source],
    text(fill: white, weight: "bold")[Primary / yr],
    text(fill: white, weight: "bold")[Partner / yr],
    text(fill: white, weight: "bold")[Combined / yr],
  ),
  [Social Security],
    [#fmt_usd(client.income.primary.social_security)],
    [#fmt_usd(client.income.partner.social_security)],
    [#fmt_usd(client.income.combined.social_security)],
  [Pension Income],
    [#fmt_usd(client.income.primary.pension)],
    [#fmt_usd(client.income.partner.pension)],
    [#fmt_usd(client.income.combined.pension)],
  [Existing Annuities],
    [#fmt_usd(client.income.primary.annuity_existing)],
    [#fmt_usd(client.income.partner.annuity_existing)],
    [#fmt_usd(client.income.combined.annuity_existing)],
  [Other Income],
    [#fmt_usd(client.income.primary.other)],
    [#fmt_usd(client.income.partner.other)],
    [#fmt_usd(client.income.combined.other)],
  table.hline(stroke: 1pt + rgb("#1d4ed8")),
  [*Total Annual Income*],
    [*#fmt_usd(client.income.primary.total)*],
    [*#fmt_usd(client.income.partner.total)*],
    [*#fmt_usd(client.income.combined.total)*],
)

#v(0.5em)

#grid(
  columns: (1fr, 1fr, 1fr),
  gutter: 0.8em,
  kpi_card("Total Annual Income",
    fmt_usd(client.income.combined.total),  sub: "At retirement"),
  kpi_card("Guaranteed Income",
    fmt_usd(client.income.combined.social_security + client.income.combined.pension),
    sub: "SS + Pension"),
  kpi_card("Variable Income",
    fmt_usd(client.income.combined.annuity_existing + client.income.combined.other),
    sub: "Annuity + Other"),
)

#note_box[
  *Income gap analysis:* If annual essential spending exceeds guaranteed income, the gap
  must be funded from the investment portfolio. Review withdrawal rate relative to the
  4 % sustainable withdrawal rule.
]

// ---------------------------------------------------------------------------
#if config.at("include_advisor_info", default: true) [
== Advisor Information

#let _adv = clients.at("advisor_info", default: (:))

#styled_table(
  columns: (auto, 1fr),
  table.header(
    text(fill: white, weight: "bold")[Field],
    text(fill: white, weight: "bold")[Value],
  ),
  [Advisor Name],    [#field(_adv, "Name")],
  [Credentials],    [#field(_adv, "Credentials")],
  [Title],          [#field(_adv, "Title")],
  [Team],           [#field(_adv, "Team")],
  [Firm],           [#field(_adv, "Firm")],
  [Email],          [#field(_adv, "Email")],
  [Phone],          [#field(_adv, "Phone_Number")],
  [Address],        [#field(_adv, "Address")],
)
] // end include_advisor_info

#pagebreak()

// ============================================================================
// SECTION 2  PORTFOLIO ANALYSIS
// ============================================================================

= Portfolio Analysis

#section_rule()

Detailed analysis of portfolio construction, performance, and strategic positioning
derived from the QWIM Analytics *Portfolios* tab.

// ---------------------------------------------------------------------------
#if config.at("include_weights_analysis", default: true) [
== Portfolio Weights Analysis

#info_box[
  *Analysis period:* #field(in_wa, "time_period") |
  *Components:* #safe_array(in_wa.at("selected_components", default: ())).join(", ") |
  *Visualisation:* #field(in_wa, "viz_type") |
  *Show %:* #field(in_wa, "show_pct")
]

#v(0.5em)

#styled_table(
  columns: (1.5fr, 1fr, 1fr, 1fr, 1fr, 1fr),
  table.header(
    text(fill: white, weight: "bold")[Asset],
    text(fill: white, weight: "bold")[Current],
    text(fill: white, weight: "bold")[Mean],
    text(fill: white, weight: "bold")[Min],
    text(fill: white, weight: "bold")[Max],
    text(fill: white, weight: "bold")[Std Dev],
  ),
  ..{
    let data = safe_array(out_wa.at("weight_statistics", default: ()))
    let rows = ()
    if data.len() == 0 {
      rows.push(table.cell(colspan: 6)[_No weight statistics data available_])
    } else {
      for row in data {
        rows.push([#field(row, "component")])
        rows.push([#fmt_pct(row.at("current_weight", default: 0.0))])
        rows.push([#fmt_pct(row.at("mean_weight", default: 0.0))])
        rows.push([#fmt_pct(row.at("min_weight", default: 0.0))])
        rows.push([#fmt_pct(row.at("max_weight", default: 0.0))])
        rows.push(
          if row.at("std_weight", default: none) != none
            { [#fmt_pct(row.std_weight)] }
          else
            { [--] }
        )
      }
    }
    rows
  }
)

#figure(
  image("outputs_images/chart_weights_analysis_portfolio_weight_distribution_over_time.svg", width: 100%),
  caption: [Portfolio Weights Analysis Over Time -- Stacked Area Chart],
)

#figure(
  image("outputs_images/chart_weights_analysis_portfolio_current_composition.svg", width: 80%),
  caption: [Current Portfolio Composition by Asset Class],
)
] // end include_weights_analysis

// ---------------------------------------------------------------------------
#if config.at("include_portfolio_analysis", default: true) [
== Portfolio Performance Analysis

#info_box[
  *Period:* #field(in_pa, "time_period") |
  *Type:* #field(in_pa, "analysis_type") |
  *Rolling window:* #field(in_pa, "rolling_window") days |
  *Includes benchmark:* #field(in_pa, "include_benchmark")
]

=== Return Distribution Statistics

#styled_table(
  columns: (2fr, 1fr, 1fr),
  table.header(
    text(fill: white, weight: "bold")[Metric],
    text(fill: white, weight: "bold")[Portfolio],
    text(fill: white, weight: "bold")[Benchmark],
  ),
  ..{
    let data = safe_array(out_pa.at("basic_statistics", default: ()))
    let rows = ()
    if data.len() == 0 {
      rows.push(table.cell(colspan: 3)[_No basic-statistics data available_])
    } else {
      for row in data {
        rows.push([#field(row, "metric")])
        rows.push([#field(row, "portfolio")])
        rows.push([#field(row, "benchmark")])
      }
    }
    rows
  }
)

=== Risk-Adjusted Performance Metrics

#styled_table(
  columns: (2.5fr, 1fr),
  table.header(
    text(fill: white, weight: "bold")[Metric],
    text(fill: white, weight: "bold")[Value],
  ),
  ..{
    let data = safe_array(out_pa.at("performance_metrics", default: ()))
    let rows = ()
    if data.len() == 0 {
      rows.push(table.cell(colspan: 2)[_No performance-metrics data available_])
    } else {
      for row in data {
        rows.push([#field(row, "metric")])
        rows.push([#field(row, "value")])
      }
    }
    rows
  }
)

#figure(
  image("outputs_images/chart_portfolio_analysis_returns_distribution.svg", width: 100%),
  caption: [Daily Returns Distribution -- Portfolio vs Benchmark],
)
] // end include_portfolio_analysis

// ---------------------------------------------------------------------------
#if config.at("include_portfolio_comparison", default: true) [
== Portfolio vs Benchmark Comparison

#info_box[
  *Period:* #field(out_pc, "time_period") |
  *From:* #field(out_pc, "start_date") |
  *To:* #field(out_pc, "end_date") |
  *Method:* #field(out_pc, "viz_type")
]

#v(0.5em)

#grid(
  columns: (1fr, 1fr, 1fr, 1fr),
  gutter: 0.8em,
  kpi_card("Portfolio Return",  fmt_pct(out_pc.metrics.total_return.portfolio),   sub: "Total period"),
  kpi_card("Benchmark Return",  fmt_pct(out_pc.metrics.total_return.benchmark),   sub: "Total period"),
  kpi_card("Sharpe Ratio",      fmt_ratio(out_pc.metrics.sharpe_ratio.portfolio), sub: "Portfolio",   accent: rgb("#0f766e")),
  kpi_card("Info Ratio",        fmt_ratio(out_pc.metrics.information_ratio),      sub: "Active mgmt", accent: rgb("#b45309")),
)

#v(0.8em)

#styled_table_teal(
  columns: (2.2fr, 1.1fr, 1.1fr, 1.1fr),
  table.header(
    text(fill: white, weight: "bold")[Metric],
    text(fill: white, weight: "bold")[Portfolio],
    text(fill: white, weight: "bold")[Benchmark],
    text(fill: white, weight: "bold")[Difference],
  ),
  [Total Return],
    [#fmt_pct(out_pc.metrics.total_return.portfolio)],
    [#fmt_pct(out_pc.metrics.total_return.benchmark)],
    [#signed_cell(out_pc.metrics.total_return.difference)],
  [Annualised Return],
    [#fmt_pct(out_pc.metrics.annualized_return.portfolio)],
    [#fmt_pct(out_pc.metrics.annualized_return.benchmark)],
    [#signed_cell(out_pc.metrics.annualized_return.difference)],
  [Volatility (Ann.)],
    [#fmt_pct(out_pc.metrics.volatility.portfolio)],
    [#fmt_pct(out_pc.metrics.volatility.benchmark)],
    [#signed_cell(out_pc.metrics.volatility.difference)],
  [Maximum Drawdown],
    [#fmt_pct(out_pc.metrics.max_drawdown.portfolio)],
    [#fmt_pct(out_pc.metrics.max_drawdown.benchmark)],
    [#signed_cell(out_pc.metrics.max_drawdown.difference)],
  [Sharpe Ratio],
    [#fmt_ratio(out_pc.metrics.sharpe_ratio.portfolio)],
    [#fmt_ratio(out_pc.metrics.sharpe_ratio.benchmark)],
    [#signed_cell(out_pc.metrics.sharpe_ratio.difference, is_pct: false)],
  [Correlation],       [--], [--], [#fmt_ratio(out_pc.metrics.correlation)],
  [Tracking Error],    [--], [--], [#fmt_pct(out_pc.metrics.tracking_error)],
  [Info Ratio],        [--], [--], [#fmt_ratio(out_pc.metrics.information_ratio)],
)

#figure(
  image("outputs_images/chart_portfolio_comparison_portfolio_vs_benchmark.svg", width: 100%),
  caption: [Portfolio vs Benchmark -- Normalised Performance (Base = 100)],
)

#note_box[
  *Interpretation:* Information Ratio of
  #fmt_ratio(out_pc.metrics.information_ratio) indicates active management value added
  relative to tracking error. Correlation of #fmt_ratio(out_pc.metrics.correlation)
  confirms consistent co-movement with benchmark.
]
] // end include_portfolio_comparison

// ---------------------------------------------------------------------------
#if config.at("include_skfolio_optimization", default: false) [
== Portfolio Optimisation (skfolio)

#info_box[
  *Period:* #field(in_sk, "time_period") |
  *Method 1:* #field(in_sk.at("method1", default: (:)), "category") -- #field(in_sk.at("method1", default: (:)), "type") |
  *Method 2:* #field(in_sk.at("method2", default: (:)), "category") -- #field(in_sk.at("method2", default: (:)), "type") -- #field(in_sk.at("method2", default: (:)), "objective")
]

#v(0.5em)

#grid(
  columns: (1fr, 1fr),
  gutter: 1.2em,
  block(fill: rgb("#eff6ff"), inset: 1em, radius: 5pt, stroke: 0.5pt + rgb("#bfdbfe"))[
    #text(weight: "bold", fill: rgb("#1d4ed8"))[Method 1 -- #out_sk.performance_summary.method1.label] \
    #v(0.4em)
    #set text(size: 10pt)
    - *Ann. Return:* #fmt_pct(out_sk.performance_summary.method1.annualized_return)
    - *Volatility:*   #fmt_pct(out_sk.performance_summary.method1.volatility)
    - *Sharpe Ratio:* #fmt_ratio(out_sk.performance_summary.method1.sharpe_ratio)
  ],
  block(fill: rgb("#f0fdf4"), inset: 1em, radius: 5pt, stroke: 0.5pt + rgb("#bbf7d0"))[
    #text(weight: "bold", fill: rgb("#15803d"))[Method 2 -- #out_sk.performance_summary.method2.label] \
    #v(0.4em)
    #set text(size: 10pt)
    - *Ann. Return:* #fmt_pct(out_sk.performance_summary.method2.annualized_return)
    - *Volatility:*   #fmt_pct(out_sk.performance_summary.method2.volatility)
    - *Sharpe Ratio:* #fmt_ratio(out_sk.performance_summary.method2.sharpe_ratio)
  ],
)

#v(0.8em)

#styled_table(
  columns: (1.5fr, 1fr, 1fr),
  table.header(
    text(fill: white, weight: "bold")[Asset],
    text(fill: white, weight: "bold")[#out_sk.performance_summary.method1.label],
    text(fill: white, weight: "bold")[#out_sk.performance_summary.method2.label],
  ),
  ..{
    let data = safe_array(out_sk.at("weights_comparison", default: ()))
    let rows = ()
    if data.len() == 0 {
      rows.push(table.cell(colspan: 3)[_No skfolio weights data available_])
    } else {
      for row in data {
        rows.push([#field(row, "asset")])
        rows.push([#fmt_pct(row.at("equal_weighted", default: 0.0))])
        rows.push([#fmt_pct(row.at("mean_risk", default: 0.0))])
      }
    }
    rows
  }
)

#v(0.6em)

#styled_table(
  columns: (1.6fr, 1fr, 1fr, 1fr),
  table.header(
    text(fill: white, weight: "bold")[Statistic],
    text(fill: white, weight: "bold")[#out_sk.performance_summary.method1.label],
    text(fill: white, weight: "bold")[#out_sk.performance_summary.method2.label],
    text(fill: white, weight: "bold")[Difference],
  ),
  ..{
    let data = safe_array(out_sk.at("statistics_comparison", default: ()))
    let rows = ()
    if data.len() == 0 {
      rows.push(table.cell(colspan: 4)[_No skfolio statistics data available_])
    } else {
      for row in data {
        let is_pct = row.at("format", default: "ratio") == "pct"
        rows.push([#field(row, "metric")])
        rows.push([
          #if is_pct {
            fmt_pct(row.at("method1", default: 0.0))
          } else {
            fmt_ratio(row.at("method1", default: 0.0))
          }
        ])
        rows.push([
          #if is_pct {
            fmt_pct(row.at("method2", default: 0.0))
          } else {
            fmt_ratio(row.at("method2", default: 0.0))
          }
        ])
        rows.push([
          #if is_pct {
            fmt_pct_signed(row.at("difference", default: 0.0))
          } else {
            signed_cell(row.at("difference", default: 0.0), is_pct: false)
          }
        ])
      }
    }
    rows
  }
)

#figure(
  image("outputs_images/chart_skfolio_optimization_portfolio_weights_comparison.svg", width: 100%),
  caption: [Optimised Portfolio Weights -- Grouped Bar Chart],
)

#figure(
  image("outputs_images/chart_skfolio_optimization_comparison_portfolio_performance.svg", width: 100%),
  caption: [Optimised Portfolio Performance -- Normalised (Base = 100)],
)
] // end include_skfolio_optimization

// ---------------------------------------------------------------------------
#if config.at("include_optimalportfolios_optimization", default: false) [
== Portfolio Optimisation (OptimalPortfolios)

#info_box[
  *Period:* #field(in_op, "time_period") |
  *Benchmark:* #field(in_op, "benchmark_key") |
  *Method 1:* #field(in_op.at("method1", default: (:)), "type") |
  *Method 2:* #field(in_op.at("method2", default: (:)), "type")
]

#v(0.5em)

#grid(
  columns: (1fr, 1fr),
  gutter: 1.2em,
  block(fill: rgb("#eff6ff"), inset: 1em, radius: 5pt, stroke: 0.5pt + rgb("#bfdbfe"))[
    #text(weight: "bold", fill: rgb("#1d4ed8"))[Method 1 -- #out_op.performance_summary.method1.label] \
    #v(0.4em)
    #set text(size: 10pt)
    - *Ann. Return:* #fmt_pct(out_op.performance_summary.method1.annualized_return)
    - *Volatility:*   #fmt_pct(out_op.performance_summary.method1.volatility)
    - *Sharpe Ratio:* #fmt_ratio(out_op.performance_summary.method1.sharpe_ratio)
  ],
  block(fill: rgb("#f0fdf4"), inset: 1em, radius: 5pt, stroke: 0.5pt + rgb("#bbf7d0"))[
    #text(weight: "bold", fill: rgb("#15803d"))[Method 2 -- #out_op.performance_summary.method2.label] \
    #v(0.4em)
    #set text(size: 10pt)
    - *Ann. Return:* #fmt_pct(out_op.performance_summary.method2.annualized_return)
    - *Volatility:*   #fmt_pct(out_op.performance_summary.method2.volatility)
    - *Sharpe Ratio:* #fmt_ratio(out_op.performance_summary.method2.sharpe_ratio)
  ],
)

#v(0.8em)

#styled_table(
  columns: (1.5fr, 1fr, 1fr),
  table.header(
    text(fill: white, weight: "bold")[Asset],
    text(fill: white, weight: "bold")[#out_op.performance_summary.method1.label],
    text(fill: white, weight: "bold")[#out_op.performance_summary.method2.label],
  ),
  ..{
    let data = safe_array(out_op.at("weights_comparison", default: ()))
    let rows = ()
    if data.len() == 0 {
      rows.push(table.cell(colspan: 3)[_No OptimalPortfolios weights data available_])
    } else {
      for row in data {
        rows.push([#field(row, "asset")])
        rows.push([#fmt_pct(row.at("method1", default: 0.0))])
        rows.push([#fmt_pct(row.at("method2", default: 0.0))])
      }
    }
    rows
  }
)

#v(0.6em)

#styled_table(
  columns: (1.6fr, 1fr, 1fr, 1fr),
  table.header(
    text(fill: white, weight: "bold")[Statistic],
    text(fill: white, weight: "bold")[#out_op.performance_summary.method1.label],
    text(fill: white, weight: "bold")[#out_op.performance_summary.method2.label],
    text(fill: white, weight: "bold")[Difference],
  ),
  ..{
    let data = safe_array(out_op.at("statistics_comparison", default: ()))
    let rows = ()
    if data.len() == 0 {
      rows.push(table.cell(colspan: 4)[_No OptimalPortfolios statistics data available_])
    } else {
      for row in data {
        let is_pct = row.at("format", default: "ratio") == "pct"
        rows.push([#field(row, "metric")])
        rows.push([
          #if is_pct {
            fmt_pct(row.at("method1", default: 0.0))
          } else {
            fmt_ratio(row.at("method1", default: 0.0))
          }
        ])
        rows.push([
          #if is_pct {
            fmt_pct(row.at("method2", default: 0.0))
          } else {
            fmt_ratio(row.at("method2", default: 0.0))
          }
        ])
        rows.push([
          #if is_pct {
            fmt_pct_signed(row.at("difference", default: 0.0))
          } else {
            signed_cell(row.at("difference", default: 0.0), is_pct: false)
          }
        ])
      }
    }
    rows
  }
)

#figure(
  image("outputs_images/chart_optimalportfolios_optimization_portfolio_weights_comparison.svg", width: 100%),
  caption: [Optimised Portfolio Weights -- Grouped Bar Chart],
)

#figure(
  image("outputs_images/chart_optimalportfolios_optimization_comparison_portfolio_performance.svg", width: 100%),
  caption: [Optimised Portfolio Performance -- Normalised (Base = 100)],
)
] // end include_optimalportfolios_optimization

#pagebreak()

// ============================================================================
// SECTION 3  SIMULATION RESULTS
// ============================================================================

#if config.at("include_simulation", default: true) [
= Monte Carlo Simulation

#section_rule()

The simulation runs #field(out_sim.summary_statistics, "num_scenarios") scenarios over
#field(out_sim.summary_statistics, "horizon_days") trading days using a
*#field(in_sim, "distribution_type")* returns model.

// ---------------------------------------------------------------------------
== Simulation Parameters

#styled_table(
  columns: (auto, 1fr),
  table.header(
    text(fill: white, weight: "bold")[Parameter],
    text(fill: white, weight: "bold")[Value],
  ),
  [Number of Scenarios],    [#field(in_sim, "num_scenarios")],
  [Horizon (trading days)], [#field(in_sim, "num_days")],
  [Initial Value],          [#fmt_usd(in_sim.at("initial_value", default: 100.0))],
  [Returns Distribution],   [#field(in_sim, "distribution_type")],
  [Assets Modelled],        [#safe_array(in_sim.at("selected_components", default: ())).join(", ")],
  [RNG Algorithm],          [#field(in_sim, "rng_type")],
  [Random Seed],            [#field(in_sim, "seed")],
)

// ---------------------------------------------------------------------------
== Terminal Value Distribution

#grid(
  columns: (1fr, 1fr, 1fr, 1fr),
  gutter: 0.8em,
  kpi_card("Initial Value",    fmt_usd(out_sim.summary_statistics.initial_value),
    sub: "Starting capital"),
  kpi_card("Median Terminal",  fmt_usd(out_sim.summary_statistics.median_terminal_value),
    sub: "50th percentile",    accent: rgb("#0f766e")),
  kpi_card("Mean Terminal",    fmt_usd(out_sim.summary_statistics.mean_terminal_value),
    sub: "Average outcome"),
  kpi_card("Prob. of Loss",    fmt_pct(out_sim.summary_statistics.probability_of_loss),
    sub: "P(end < initial)",   accent: rgb("#b91c1c")),
)

#v(0.8em)

#styled_table(
  columns: (2fr, 1fr, 1fr),
  table.header(
    text(fill: white, weight: "bold")[Statistic],
    text(fill: white, weight: "bold")[Terminal Value],
    text(fill: white, weight: "bold")[vs Initial],
  ),
  [5th Pct -- Stress Scenario],
    [#fmt_usd(out_sim.summary_statistics.percentile_5)],
    [#signed_cell(safe_div(out_sim.summary_statistics.percentile_5 - out_sim.summary_statistics.initial_value, out_sim.summary_statistics.initial_value))],
  [25th Pct -- Adverse],
    [#fmt_usd(out_sim.summary_statistics.percentile_25)],
    [#signed_cell(safe_div(out_sim.summary_statistics.percentile_25 - out_sim.summary_statistics.initial_value, out_sim.summary_statistics.initial_value))],
  [Median (50th Pct)],
    [#fmt_usd(out_sim.summary_statistics.median_terminal_value)],
    [#signed_cell(safe_div(out_sim.summary_statistics.median_terminal_value - out_sim.summary_statistics.initial_value, out_sim.summary_statistics.initial_value))],
  [Mean],
    [#fmt_usd(out_sim.summary_statistics.mean_terminal_value)],
    [#signed_cell(safe_div(out_sim.summary_statistics.mean_terminal_value - out_sim.summary_statistics.initial_value, out_sim.summary_statistics.initial_value))],
  [75th Pct -- Favourable],
    [#fmt_usd(out_sim.summary_statistics.percentile_75)],
    [#signed_cell(safe_div(out_sim.summary_statistics.percentile_75 - out_sim.summary_statistics.initial_value, out_sim.summary_statistics.initial_value))],
  [95th Pct -- Optimistic],
    [#fmt_usd(out_sim.summary_statistics.percentile_95)],
    [#signed_cell(safe_div(out_sim.summary_statistics.percentile_95 - out_sim.summary_statistics.initial_value, out_sim.summary_statistics.initial_value))],
  table.hline(stroke: 0.8pt + rgb("#1d4ed8")),
  [Standard Deviation],  [#fmt_usd(out_sim.summary_statistics.std_dev_terminal_value)], [--],
  [Minimum],
    [#fmt_usd(out_sim.summary_statistics.min_terminal_value)],
    [#signed_cell(safe_div(out_sim.summary_statistics.min_terminal_value - out_sim.summary_statistics.initial_value, out_sim.summary_statistics.initial_value))],
  [Maximum],
    [#fmt_usd(out_sim.summary_statistics.max_terminal_value)],
    [#signed_cell(safe_div(out_sim.summary_statistics.max_terminal_value - out_sim.summary_statistics.initial_value, out_sim.summary_statistics.initial_value))],
)

#figure(
  image("outputs_images/chart_simulation_portfolio_value_fan_chart.svg", width: 100%),
  caption: [Monte Carlo Fan Chart -- Portfolio Value Paths over Simulation Horizon],
)

#figure(
  image("outputs_images/chart_simulation_terminal_value_distribution.svg", width: 90%),
  caption: [Terminal Value Distribution -- Histogram with Mean (orange) and Median (green)],
)

#note_box[
  *Risk summary:* #fmt_pct(out_sim.summary_statistics.probability_of_loss) probability
  of portfolio declining below initial value. IQR spans
  #fmt_usd(out_sim.summary_statistics.percentile_25) --
  #fmt_usd(out_sim.summary_statistics.percentile_75).
  *Simulation results are illustrative and do not constitute projections or investment
  advice.*
]
] // end include_simulation

#pagebreak()

#if config.at("include_goal_parity", default: true) [
= Your Goal Parity Portfolio

#section_rule()

Your portfolio is built around four goals that work together to support your
financial life:

#grid(
  columns: (1fr, 1fr, 1fr, 1fr),
  gutter: 0.6em,
  [*Liquidity* \ Cash you can access quickly if you need it],
  [*Income* \ Regular, dependable payments],
  [*Preservation* \ Protecting what you've already saved],
  [*Growth* \ Building wealth over the long run],
)

#v(0.5em)

Instead of picking investments one at a time, your portfolio was built so
that all four goals are supported together -- based on how long you're
investing for and how comfortable you are with ups and downs along the way.

// ---------------------------------------------------------------------------
== Your Profile

#styled_table(
  columns: (auto, 1fr),
  table.header(
    text(fill: white, weight: "bold")[ ],
    text(fill: white, weight: "bold")[ ],
  ),
  [Time Horizon],            [#field(in_gp, "strategic_horizon_years") years],
  [Review Frequency],        [Every #field(in_gp, "rebalancing_frequency_months") months],
  [Risk Comfort Level],      [#field(in_gp, "risk_profile")],
  [Comfort with a Market Downturn],
    [Comfortable with a decline of up to #fmt_pct(in_gp.at("loss_tolerance", default: 0.0)) before adjusting course],
)

// ---------------------------------------------------------------------------
== How Your Portfolio Supports Each Goal

#if not out_gp.solver_success [
#note_box[
  *Please note:* the portfolio shown below did not fully converge during
  calculation. The figures are the best result found and are usually still
  reasonable, but we recommend confirming this allocation with your advisor
  before acting on it.
]
]

#if out_gp.scarce_goals.len() > 0 [
#note_box[
  *Please note:* #out_gp.scarce_goals.join(" and ") has limited support in
  the current investment universe — no single holding scores highly enough
  on this goal to power it much further, regardless of how the portfolio is
  tilted. A low score here reflects the range of available investments, not
  a shortfall in the optimization.
]
]

#grid(
  columns: (1fr, 1fr, 1fr, 1fr),
  gutter: 0.8em,
  kpi_card("Liquidity", fmt_pct(out_gp.goal_powers.Liquidity), sub: "Balanced target: 25%"),
  kpi_card("Income", fmt_pct(out_gp.goal_powers.Income), sub: "Balanced target: 25%",
    accent: rgb("#0f766e")),
  kpi_card("Preservation", fmt_pct(out_gp.goal_powers.Preservation), sub: "Balanced target: 25%"),
  kpi_card("Growth", fmt_pct(out_gp.goal_powers.Growth), sub: "Balanced target: 25%",
    accent: rgb("#b91c1c")),
)

#v(0.8em)

*Expected annual return:* #fmt_pct(out_gp.at("expected_return", default: 0.0))

#figure(
  image("outputs_images/chart_goal_parity_goal_powers.svg", width: 90%),
  caption: [How your portfolio supports each goal, compared to an evenly balanced target],
)

#if out_gp.top_weights.len() > 0 [
== What You're Invested In

#styled_table(
  columns: (1fr, 1fr),
  table.header(
    text(fill: white, weight: "bold")[Investment],
    text(fill: white, weight: "bold")[% of Portfolio],
  ),
  ..out_gp.top_weights.map(row => (
    [#row.at("name", default: row.at("ticker", default: "N/A"))],
    [#fmt_pct(row.at("weight", default: 0.0))],
  )).flatten()
)

#figure(
  image("outputs_images/chart_goal_parity_weights.svg", width: 90%),
  caption: [Your portfolio's current holdings],
)
] else [
#note_box[No portfolio holdings available.]
]

// ---------------------------------------------------------------------------
== Keeping Your Portfolio on Track

#if out_gp.rebalancing.traded [
#note_box[
  *Your portfolio was recently rebalanced:* #field(out_gp.rebalancing, "num_trades")
  trades were made, adjusting about #fmt_pct(out_gp.rebalancing.at("turnover", default: 0.0))
  of the portfolio, to keep it aligned with your goals as markets moved.
]
] else [
#note_box[
  *No adjustments were needed:* your portfolio remains well-aligned with your
  goals, so no trades were made at this time. This helps avoid unnecessary
  costs from over-trading.
]
]

#note_box[
  This approach is based on the Goal Parity framework (Golts & Jones, 2023),
  a peer-reviewed academic methodology for building portfolios around an
  investor's personal goals rather than a one-size-fits-all objective.
  *Results are illustrative and do not constitute investment advice.*
]
] // end include_goal_parity

#pagebreak()

// ============================================================================
// SECTION 4  EXECUTIVE SUMMARY
// ============================================================================

= Executive Summary

#section_rule()

// Summary KPI banner
#block(fill: rgb("#1d4ed8"), inset: (x: 1.2em, y: 0.9em), radius: 5pt)[
  #set text(fill: white)
  #grid(
    columns: (1fr, 1fr, 1fr, 1fr),
    gutter: 1em,
    align: center,
    [
      #text(weight: "bold", size: 18pt)[#fmt_usd(client.assets.combined.total)] \
      #text(size: 9pt)[Total Assets]
    ],
    [
      #text(weight: "bold", size: 18pt)[#fmt_usd(client.income.combined.total)] \
      #text(size: 9pt)[Annual Retirement Income]
    ],
    [
      #text(weight: "bold", size: 18pt)[#fmt_pct(out_pc.metrics.annualized_return.portfolio)] \
      #text(size: 9pt)[Portfolio Ann. Return]
    ],
    [
      #text(weight: "bold", size: 18pt)[#fmt_ratio(out_pc.metrics.sharpe_ratio.portfolio)] \
      #text(size: 9pt)[Sharpe Ratio]
    ],
  )
]

#v(0.8em)

== Key Findings

+ *Asset Sufficiency* -- Combined assets of #fmt_usd(client.assets.combined.total)
  against total goals of #fmt_usd(client.goals.combined.total) gives a wealth coverage
  ratio of #fmt_pct(safe_div(client.assets.combined.total, client.goals.combined.total)).
  #sufficiency_badge(safe_div(client.assets.combined.total, client.goals.combined.total))

+ *Portfolio Outperformance* -- The portfolio achieved
  #fmt_pct(out_pc.metrics.total_return.portfolio) total return over
  #field(out_pc, "time_period"), vs benchmark return of
  #fmt_pct(out_pc.metrics.total_return.benchmark). Information Ratio:
  #fmt_ratio(out_pc.metrics.information_ratio).

+ *Optimisation Results* -- Mean-risk portfolio (Method 2) achieved Sharpe
  #fmt_ratio(out_sk.performance_summary.method2.sharpe_ratio) vs
  #fmt_ratio(out_sk.performance_summary.method1.sharpe_ratio) for equal-weighted.
  Volatility reduced from #fmt_pct(out_sk.performance_summary.method1.volatility) to
  #fmt_pct(out_sk.performance_summary.method2.volatility).

+ *Guaranteed Income Floor* -- Social Security + Pension of
  #fmt_usd(client.income.combined.social_security + client.income.combined.pension) p.a.
  is not subject to market risk.

+ *Simulation Risk* -- #fmt_pct(out_sim.summary_statistics.probability_of_loss)
  probability of loss over #field(out_sim.summary_statistics, "horizon_days") trading days.

== Planning Priorities

#list(
  [*Tax location:* Evaluate Roth conversions before age 73 to manage RMD exposure
   from tax-deferred balance of #fmt_usd(client.assets.combined.tax_deferred).],
  [*Income gap:* Quantify annual shortfall vs guaranteed income
   (#fmt_usd(client.income.combined.social_security + client.income.combined.pension) p.a.).],
  [*Drawdown protection:* Review downside strategies given
   #fmt_pct(out_pc.metrics.max_drawdown.portfolio) historical max drawdown.],
  [*Annual rebalancing:* Maintain target weights to capture the rebalancing premium.],
  [*Longevity planning:* Stress-test withdrawal rates over 95-year horizon.],
  [*Withdrawal rate:* Validate 4 % assumption given current Sharpe of
   #fmt_ratio(out_pc.metrics.sharpe_ratio.portfolio).],
)

// ============================================================================
// SECTION 5 — DISCLOSURES
// ============================================================================

#pagebreak()

= Disclosures

#section_rule()

#set text(size: 9.5pt, fill: rgb("#374151"))

== Methodology

Portfolio performance metrics use daily total-return data. Annualised figures assume
252 trading days per year. The Sharpe Ratio uses a 2 % nominal risk-free rate.
Maximum Drawdown is the largest peak-to-trough percentage decline within the analysis
window. Portfolio optimisation uses the skfolio library implementing convex and
classical portfolio optimisation methods.

== Monte Carlo Disclaimer

Simulation results are illustrative only and do not constitute projections of actual
future portfolio values. Outcomes depend on assumed return distributions, calibration
data, and parameter choices. Actual results may differ materially.

== Important Notice

#note_box[
  *Past performance is not indicative of future results.* This report is for
  informational and planning purposes only and does not constitute investment advice,
  a solicitation, or an offer to buy or sell any security. All figures are based on
  data provided through the QWIM Analytics platform and have not been independently
  verified. Consult a qualified financial advisor before making investment decisions.

  Report date: *#meta.report_date* | Version: #meta.report_version |
  Generated by: #meta.generated_by
]