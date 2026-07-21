

// ============================================================================
// 1.  HELPER FUNCTIONS
// ============================================================================

// ---- insert commas every three digits ------------------------------------
#let _add_commas(s) = {
  let clusters = s.clusters()
  let n        = clusters.len()
  let out      = ()
  for i in range(n) {
    if i > 0 and calc.rem(n - i, 3) == 0 { out.push(",") }
    out.push(clusters.at(i))
  }
  out.join("")
}

// ---- safe integer conversion (guards "N/A" / none / float strings) ---------
// Defined early so all subsequent helpers can use it without forward-reference.
#let safe_int(val, default: 0) = {
  if val == none or val == "N/A" or val == "" { return default }
  // JSON often delivers numbers as floats (60.0) or float-strings ("60.0").
  // Typst's int() rejects float-strings, so we parse through float() first.
  if type(val) == int { return val }
  if type(val) == float { return int(val) }
  // val is a string — try float() then truncate to int to handle "60.0"
  let v = float(val)
  int(v)
}

// ---- safe float conversion (guards "N/A" / none) -------------------------
#let safe_num(val, default: 0.0) = {
  if val == none or val == "N/A" or val == "" { return default }
  if type(val) == str { float(val) } else { float(val) }
}

// ---- safe division (guards zero denominator / none) ----------------------
#let safe_div(a, b, default: 0.0) = {
  if a == none or b == none { return default }
  let bv = if type(b) == str { float(b) } else { float(b) }
  if bv == 0.0 { return default }
  let av = if type(a) == str { float(a) } else { float(a) }
  av / bv
}

// ---- format float / int as USD ($1,234,567) ------------------------------
#let fmt_usd(val) = {
  if val == none or val == "N/A" or val == "" { return "$0" }
  let v = if type(val) == str { float(val) } else { float(val) }
  if v == 0.0 { return "$0" }
  let neg       = v < 0
  let n         = calc.round(calc.abs(v))  // always a Typst float
  let formatted = _add_commas(str(int(n))) // int(float) is safe in Typst
  if neg { "-$" + formatted } else { "$" + formatted }
}

// ---- format float as percentage (0.1842 -> "18.42 %") -------------------
#let fmt_pct(val) = {
  if val == none or val == "N/A" or val == "" { return "N/A" }
  let v = if type(val) == str { float(val) } else { float(val) }
  let p = calc.round(v * 100, digits: 2)
  str(p) + " %"
}

// ---- format float as percentage with explicit sign (+2.80 %) -------------
#let fmt_pct_signed(val) = {
  if val == none or val == "N/A" or val == "" { return "N/A" }
  let v = if type(val) == str { float(val) } else { float(val) }
  let p = calc.round(v * 100, digits: 2)
  if v >= 0 { "+" + str(p) + " %" } else { str(p) + " %" }
}

// ---- format ratio to 2 decimal places ------------------------------------
#let fmt_ratio(val) = {
  if val == none or val == "N/A" or val == "" { return "N/A" }
  let v = if type(val) == str { float(val) } else { float(val) }
  str(calc.round(v, digits: 2))
}

// ---- safe field access with fallback -------------------------------------
#let field(obj, key, fallback: "N/A") = {
  if obj == none { return fallback }
  let v = obj.at(key, default: none)
  if v == none or v == ""  { fallback }
  else if type(v) == bool { if v { "Yes" } else { "No" } }
  else               { str(v) }
}

// ---- green / red signed cell ---------------------------------------------
#let signed_cell(v, is_pct: true) = {
  let fmt       = if is_pct { fmt_pct_signed(v) } else { fmt_ratio(v) }
  let col       = if safe_num(v) >= 0 { rgb("#15803d") } else { rgb("#b91c1c") }
  text(fill: col, weight: "bold", fmt)
}

// ---- risk profile badge (colour-coded) -----------------------------------
#let risk_badge(level) = {
  let col = if level == "Conservative"  { rgb("#0f766e") }
       else if level == "Moderate"      { rgb("#b45309") }
       else if level == "Aggressive"    { rgb("#b91c1c") }
       else                             { rgb("#374151") }
  box(
    fill: col.lighten(80%),
    inset: (x: 0.45em, y: 0.2em),
    radius: 3pt,
    stroke: 0.5pt + col,
  )[#text(fill: col, weight: "bold", size: 9pt)[#level]]
}

// ---- wealth sufficiency badge (green / amber / red) ----------------------
#let sufficiency_badge(ratio) = {
  let v   = safe_num(ratio)
  let col = if v >= 1.0 { rgb("#15803d") }
       else if v >= 0.7  { rgb("#b45309") }
       else               { rgb("#b91c1c") }
  let lbl = if v >= 1.0 { "FUNDED" }
       else if v >= 0.7  { "UNDER-FUNDED" }
       else               { "DEFICIT" }
  box(
    fill: col.lighten(80%),
    inset: (x: 0.5em, y: 0.22em),
    radius: 3pt,
    stroke: 0.5pt + col,
  )[#text(fill: col, weight: "bold", size: 9pt)[#lbl]]
}