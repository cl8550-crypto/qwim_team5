#import "utils_colors.typ": *

// G1: Connections, style regular, size 10pt, color black 40%, case ALL CAPS, leading 12pt, tracking 0
#let font-g1(input_content) = [
  #set par(leading: 12pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_cool_gray,
    tracking: 0pt,
    style: "normal",
    weight: "regular",
    upper(input_content)
  )
]

// G2: Connections, style regular, 24pt, color Pantone 28, leading 24
#let font-g2(input_content) = [
  #set par(leading: 24pt)
  #text(
    font: "Arial",
    size: 24pt,
    fill: color_pantone_280,
    tracking: 0pt,
    style: "normal",
    weight: "regular",
    input_content)
]

// G3: Connections, style regular, 12pt, color black, leading 14.4pt
#let font-g3(input_content) = [
  #set par(leading: 14.4pt)
  #text(
  font: "Arial",
  size: 12pt,
  fill: color_black,
  tracking: 0pt,
  style: "normal",
  weight: "regular",
  input_content)
]

// G4: Connections, style Bold, 12pt, color white, leading 14.4pt
#let font-g4(input_content) = [
  #set par(leading: 14.4pt)
  #text(
    font: "Arial",
    size: 12pt,
    fill: color_white,
    style: "normal",
    weight: "bold",
    tracking: 0pt,
    input_content)
]

// G5: Connections Light, style Regular, size 8pt, color black, leading 9.6pt, tracking -20pt
#let font-g5(input_content) = [
  #set par(leading: 9.6pt)
  #text(
    font: "Arial",
    size: 8pt,
    fill: color_black,
    style: "normal",
    weight: "light",
    tracking: -20pt,
    input_content)
]

// G6: Connections, style Bold, size 12pt, color black, leading 15pt
#let font-g6(input_content) = [
  #set par(leading: 15pt)
  #text(
    font: "Arial",
    size: 12pt,
    fill: color_black,
    style: "normal",
    weight: "bold",
    tracking: 0pt,
    input_content)
]

// G7: Connections, style Regular, size 12pt, color black, case "title case", leading 15pt
#let font-g7(input_content) = [
  #set par(leading: 15pt)
  #text(
    font: "Arial",
    size: 12pt,
    fill: color_black,
    tracking: 0pt,
    style: "normal",
    weight: "regular",
    input_content)
]

// G8: Connections Cond Light, style Regular, size 12pt, color black, case "sentence case", leading 9.6pt, space after 0.0625""
#let font-g8(input_content) = [
  #set par(leading: 9.6pt)
  #text(
    font: "Arial",
    size: 12pt,
    fill: color_black,
    tracking: 0pt,
    style: "normal",
    weight: "light",
    stretch: 75%,
    input_content)
  
  #v(0.0625in)
]

// G9: Connections, style bold, size 14pt, color pantone 280, case "sentence case", leading 16pt
#let font-g9(input_content) = [
  #set par(leading: 16pt)
  #text(
    font: "Arial",
    size: 14pt,
    fill: color_pantone_280,
    tracking: 0pt,
    style: "normal",
    weight: "bold",
    input_content)
]

// G10: Connections, style regular, size 32pt, color pantone 280, case "title case", leading 36pt
#let font-g10(input_content) = [
  #set par(leading: 36pt)
  #text(
    font: "Arial",
    size: 32pt,
    fill: color_pantone_280,
    tracking: 0pt,
    style: "normal",
    weight: "regular",
    input_content)
]

// G11: Connections, style regular, size 12pt, color pantone 280, case "small caps", leading 15pt, tracking 25pt
#let font-g11(input_content) = [
  #set par(leading: 15pt)
  #text(
    font: "Arial",
    size: 12pt,
    fill: color_pantone_280,
    tracking: 25pt,
    style: "normal",
    weight: "regular",
    smallcaps(input_content))
]

// G12: Connections Cond Bold, style regular, size 8pt, color black, case "sentence case", leading 9.6pt, tracking 0pt
#let font-g12(input_content) = [
  #set par(leading: 9.6pt)
  #text(
    font: "Arial",
    size: 8pt,
    fill: color_black,
    tracking: 0pt,
    style: "normal",
    weight: "bold",
    stretch: 75%,
    input_content)
]

// G13: Connections Cond Bold, style italic, size 8pt, color black, case "sentence case", leading 9.6pt, tracking 0pt
#let font-g13(input_content) = [
  #set par(leading: 9.6pt)
  #text(
    font: "Arial",
    size: 8pt,
    fill: color_black,
    tracking: 0pt,
    weight: "bold",
    style: "italic",
    stretch: 75%,
    input_content)
]

// G14: Connections Light, style regular, size 10pt, color black, case "sentence case", leading 9.6pt, tracking 0pt
#let font-g14(input_content) = [
  #set par(leading: 9.6pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_black,
    tracking: 0pt,
    weight: "light",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G15: Connections Light, style regular, size 12pt, color black, case "sentence case", leading 12pt, tracking 0pt
#let font-g15(input_content) = [
  #set par(leading: 12pt)
  #text(
    font: "Arial",
    size: 12pt,
    fill: color_black,
    tracking: 0pt,
    weight: "light",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G16: Connections, style bold, size 20pt, color white, case "sentence case", leading 24pt, tracking 0pt
#let font-g16(input_content) = [
  #set par(leading: 24pt)
  #text(
    font: "Arial",
    size: 20pt,
    fill: color_white,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G17: Connections Cond Light, style italic, size 8pt, color black, case "sentence case", leading 9.6pt, tracking 0pt
#let font-g17(input_content) = [
  #set par(leading: 9.6pt)
  #text(
    font: "Arial",
    size: 8pt,
    fill: color_black,
    tracking: 0pt,
    weight: "regular",
    style: "italic",
    stretch: 75%,
    input_content)
]

// G18: Connections, style regular, size 12pt, color pantone 280, case "sentence case", leading 15pt, tracking 0pt
#let font-g18(input_content) = [
  #set par(leading: 15pt)
  #text(
    font: "Arial",
    size: 12pt,
    fill: color_pantone_280,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G19: Connections, style regular, size 11pt, color black, case "sentence case", leading 15pt, tracking 0pt
#let font-g19(input_content) = [
  #set par(leading: 15pt)
  #text(
    font: "Arial",
    size: 11pt,
    fill: color_black,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G20: Connections Cond Light, style regular, size 8pt, color black, case "sentence case", leading 9pt, tracking 0pt, underlined
#let font-g20(input_content) = [
  #set par(leading: 9pt)
  #text(
    font: "Arial",
    size: 8pt,
    fill: color_black,
    tracking: 0pt,
    weight: "light",
    style: "normal",
    stretch: 75%,
    underline(input_content))
]

// G21: Connections, style bold, size 11pt, color black, case "sentence case", leading 9.6pt, tracking -30pt
#let font-g21(input_content) = [
  #set par(leading: 9.6pt)
  #text(
    font: "Arial",
    size: 8pt,
    fill: color_black,
    tracking: -30pt,
    weight: "bold",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G22: Connections, style bold, size 12pt, color white, case "sentence case", leading 14.4pt, tracking 0pt
#let font-g22(input_content) = [
  #set par(leading: 14.4pt)
  #text(
    font: "Arial",
    size: 12pt,
    fill: color_white,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G23: Connections Cond bold, style regular, size 10pt, color black, case "title case", leading 11pt, tracking -20pt
#let font-g23(input_content) = [
  #set par(leading: 11pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_black,
    tracking: -20pt,
    weight: "bold",
    style: "normal",
    stretch: 75%,
    input_content)
]

// G24: Connections Cond Light, style regular, size 10pt, color black, case "sentence case", leading 11pt, tracking -20pt
#let font-g24(input_content) = [
  #set par(leading: 11pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_black,
    tracking: -20pt,
    weight: "light",
    style: "normal",
    stretch: 75%,
    input_content)
]

// G25: Connections Light, style regular, size 12pt, color black, case "sentence case", leading 15pt, tracking -20pt
#let font-g25(input_content) = [
  #set par(leading: 15pt)
  #text(
    font: "Arial",
    size: 12pt,
    fill: color_black,
    tracking: -20pt,
    weight: "light",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G26: Connections, style bold, size 10pt, color black, case "sentence case", leading 12pt, tracking 0pt
#let font-g26(input_content) = [
  #set par(leading: 12pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_black,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G27: Connections, style bold, size 14pt, color black, case "sentence case", leading 16.8pt, tracking 0pt
#let font-g27(input_content) = [
  #set par(leading: 16.8pt)
  #text(
    font: "Arial",
    size: 14pt,
    fill: color_black,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G28: Connections Light, style regular, size 9pt, color black, case "sentence case", leading 11pt, tracking 0pt
#let font-g28(input_content) = [
  #set par(leading: 11pt)
  #text(
    font: "Arial",
    size: 9pt,
    fill: color_black,
    tracking: 0pt,
    weight: "light",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G29: Connections, style bold, size 11pt, color black, case "sentence case", leading 10.8pt, tracking 0pt
#let font-g29(input_content) = [
  #set par(leading: 10.8pt)
  #text(
    font: "Arial",
    size: 9pt,
    fill: color_black,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G30: Connections light, style regular, size 10pt, color black, case "sentence case", leading 13pt, tracking 0pt
#let font-g30(input_content) = [
  #set par(leading: 13pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_black,
    tracking: 0pt,
    weight: "light",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G31: Connections, style regular, size 12pt, color pantone 280, case "sentence case", leading 14.4pt, tracking 0pt
#let font-g31(input_content) = [
  #set par(leading: 14.4pt)
  #text(
    font: "Arial",
    size: 12pt,
    fill: color_pantone_280,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G32: Connections, style bold, size 9pt, color black, case "title case", leading 10.8pt, tracking 0pt
#let font-g32(input_content) = [
  #set par(leading: 10.8pt)
  #text(
    font: "Arial",
    size: 9pt,
    fill: color_black,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G33: Connections Light, style regular, size 9pt, color black, case "sentence case", leading 10.8pt, tracking 0pt
#let font-g33(input_content) = [
  #set par(leading: 10.8pt)
  #text(
    font: "Arial",
    size: 9pt,
    fill: color_black,
    tracking: 0pt,
    weight: "light",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G34: Connections Light, style italic, size 8pt, color black, case "sentence case", leading 9.6pt, tracking -20pt
#let font-g34(input_content) = [
  #set par(leading: 9.6pt)
  #text(
    font: "Arial",
    size: 8pt,
    fill: color_black,
    tracking: 0pt,
    weight: "light",
    style: "italic",
    stretch: 100%,
    input_content)
]

// G35: Connections, style regular, size 9pt, color pantone 280, case "sentence case", leading 12pt, tracking 0pt
#let font-g35(input_content) = [
  #set par(leading: 15pt)
  #text(
    font: "Arial",
    size: 9pt,
    fill: color_pantone_280,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G35: Connections, style regular, size 9pt, color black, case "sentence case", leading 12pt, tracking 0pt
#let font-g35-black(input_content) = [
  #set par(leading: 15pt)
  #text(
    font: "Arial",
    size: 9pt,
    fill: color_black,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G36: Connections Light, style italic, size 11pt, color black, case "sentence case", leading 12pt, tracking 0pt
#let font-g36(input_content) = [
  #set par(leading: 12pt)
  #text(
    font: "Arial",
    size: 11pt,
    fill: color_black,
    tracking: 0pt,
    weight: "light",
    style: "italic",
    stretch: 100%,
    input_content)
]

// G37: Wingdings 2, style regular, size 9.5pt, color pantone 2925 20%, case "sentence case", leading 11.4pt, tracking 0pt
#let font-g37(input_content) = [
  #set par(leading: 15pt)
  #text(
    font: "Wingdings 2",
    size: 9.5pt,
    fill: color_pantone_2925_20,
    tracking: 11.4pt,
    weight: "regular",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G38: Connections Light, style italic, size 9pt, color black, case "sentence case", leading 10.8pt, tracking 0pt
#let font-g38(input_content) = [
  #set par(leading: 10.8pt)
  #text(
    font: "Arial",
    size: 9pt,
    fill: color_black,
    tracking: 0pt,
    weight: "light",
    style: "italic",
    stretch: 100%,
    input_content)
]

// G39: Connections, style bold, size 18pt, color black, case "sentence case", leading 20pt, tracking 0pt
#let font-g39(input_content) = [
  #set par(leading: 20pt)
  #text(
    font: "Arial",
    size: 18pt,
    fill: color_black,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G40: Connections, style bold, size 12pt, color pantone 280, case "sentence case", leading 14pt, tracking 0pt
#let font-g40(input_content) = [
  #set par(leading: 14pt)
  #text(
    font: "Arial",
    size: 12pt,
    fill: color_pantone_280,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G41: Connections, style bold, size 10pt, color black, case "sentence case", leading 13pt, tracking 0pt
#let font-g41(input_content) = [
  #set par(leading: 13pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_black,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G42: Connections, style regular, size 10pt, color black, case "sentence case", leading 13pt, tracking 0pt
#let font-g42(input_content) = [
  #set par(leading: 13pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_black,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G43: Connections, style regular, size 14pt, color black, case "sentence case", leading 16pt, tracking 0pt
#let font-g43(input_content) = [
  #set par(leading: 16pt)
  #text(
    font: "Arial",
    size: 14pt,
    fill: color_black,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G44: Connections, style regular, size 11pt, color black, case "sentence case", leading 13pt, tracking 0pt, space after 0.0625"
#let font-g19(input_content) = [
  #set par(leading: 13pt)
  #text(
    font: "Arial",
    size: 11pt,
    fill: color_black,
    tracking: 11pt,
    weight: "regular",
    style: "normal",
    stretch: 100%,
    input_content)
    
  #v(0.0625in)
]

// G45: Connections, style bold, size 11pt, color black, case "sentence case", leading 13pt, tracking 0pt
#let font-g45(input_content) = [
  #set par(leading: 11pt)
  #text(
    font: "Arial",
    size: 13pt,
    fill: color_black,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G46: Connections, style regular, size 11pt, color black, case "sentence case", leading 13pt, tracking 0pt
#let font-g46(input_content) = [
  #set par(leading: 13pt)
  #text(
    font: "Arial",
    size: 11pt,
    fill: color_black,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    stretch: 100%,
    input_content)
]

// G47: Connections, style regular, size 10pt, color black, case "sentence case", leading 12pt, tracking 0pt, space after 0.125"
#let font-g47(input_content) = [
  #set par(leading: 12pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_black,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    stretch: 100%,
    input_content)
    
  #v(0.125in)
]


//Table type styles
// T1: Connections,  Bold, 10pt, Black, leading 11, tracking 0
#let font-t1(input_content) = [
  #set par(leading: 11pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_black,
    tracking: 0pt,
    weight: "bold",
    stretch: 100%, 
    input_content
  )
]

// T2: Connections Cond Light, Regular, 10pt, Black, leading 12 pt, tracking 0pt
#let font-t2(input_content) = [
  #set par(leading: 12pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_black,
    tracking: 0pt,
    weight: "light",
    style: "normal",
    stretch: 75%, 
    input_content
  )
]

// T2 extra: Connections, Regular, 10pt, Black, leading 12 pt, tracking 0pt
#let font-t2_extra(input_content) = [
  #set par(leading: 12pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_black,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// T3: Connections Cond Bold, Regular, 10pt, White, leading 10 pt, tracking 0pt
#let font-t3(input_content) = [
  #set par(leading: 10pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_white,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 75%, 
    input_content
  )
]

// T4: Connections Cond Bold, Regular, 10pt, Black, leading 10 pt, tracking 0pt
#let font-t4(input_content) = [
  #set par(leading: 10pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_black,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 75%, 
    input_content
  )
]

// T5: Connections,  Bold, 10pt, Pantone 280, leading 11, tracking 0
#let font-t5(input_content) = [
  #set par(leading: 11pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_pantone_280,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// T6: Connections,  Bold, 10pt, Pantone 293, leading 11, tracking 0
#let font-t6(input_content) = [
  #set par(leading: 11pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_pantone_293,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// T7: Connections,  Bold, 10pt, Pantone 285, leading 11, tracking 0
#let font-t7(input_content) = [
  #set par(leading: 11pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_pantone_285,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// T8: Connections Cond Bold,  Regular, 10pt, Pantone 280, leading 11, tracking 0
#let font-t8(input_content) = [
  #set par(leading: 11pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_pantone_280,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 75%, 
    input_content
  )
]

// T9: Connections Cond Bold,  Regular, 10pt, Pantone 293, leading 11, tracking 0
#let font-t9(input_content) = [
  #set par(leading: 11pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_pantone_293,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 75%, 
    input_content
  )
]

// T10: Connections Cond Bold,  Regular, 10pt, Pantone 285, leading 11, tracking 0
#let font-t10(input_content) = [
  #set par(leading: 11pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_pantone_285,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 75%, 
    input_content
  )
]

// T11: Connections Cond Light,  Regular, 10pt, Black, leading 12, tracking 0
#let font-t11(input_content) = [
  #set par(leading: 12pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_black,
    tracking: 0pt,
    weight: "light",
    style: "normal",
    stretch: 75%, 
    input_content
  )
]

// T12: Connections, Bold, 14pt, White, leading 14 pt, tracking 0pt
#let font-t12(input_content) = [
  #set par(leading: 14pt)
  #text(
    font: "Arial",
    size: 14pt,
    fill: color_white,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// T13: Connections, Bold, 12pt, Black, leading 14.4 pt, tracking 0pt
#let font-t13(input_content) = [
  #set par(leading: 14.4pt)
  #text(
    font: "Arial",
    size: 12pt,
    fill: color_black,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 75%, 
    input_content
  )
]

// T14: Connections, Regular, 10pt, Black, leading 12 pt, tracking 0pt
#let font-t14(input_content) = [
  #set par(leading: 12pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_black,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// T15: Connections,  Bold, 10pt, Black, leading 12 pt, tracking 0pt
#let font-t15(input_content) = [
  #set par(leading: 12pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_black,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// T16: Connections,  Bold, 10pt, White, leading 12, tracking 0
#let font-t16(input_content) = [
  #set par(leading: 12pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_white,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// T17: Connections Light,  Regular, 10pt, Black, leading 12, tracking 0
#let font-t17(input_content) = [
  #set par(leading: 12pt)
  #text(
    font: "Connections Light",
    size: 10pt,
    fill: color_black,
    tracking: 0pt,
    weight: "light",
    style: "normal",
    stretch: 75%, 
    input_content
  )
]

// T18: Connections Bold,  Regular, 20pt, White, leading 24, tracking 0
#let font-t18(input_content) = [
  #set par(leading: 24pt)
  #text(
    font: "Arial",
    size: 20pt,
    fill: color_white,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// T19: Connections,  Bold, 12pt, Black, leading 14, tracking 0
#let font-t19(input_content) = [
  #set par(leading: 12pt)
  #text(
    font: "Arial",
    size: 12pt,
    fill: color_black,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// T20: Connections,  Bold, 12pt, White, leading 14, tracking 0
#let font-t20(input_content) = [
  #set par(leading: 14pt)
  #text(
    font: "Arial",
    size: 12pt,
    fill: color_white,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// T20 extra: Connections,  Bold, 11pt, White, leading 12, tracking 0
#let font-t20_extra(input_content) = [
  #set par(leading: 12pt)
  #text(
    font: "Arial",
    size: 11pt,
    fill: color_white,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// T21: Connections Cond  Bold, Regular, 10pt, White, leading 12, tracking 0
#let font-t21(input_content) = [
  #set par(leading: 12pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_white,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 75%, 
    input_content
  )
]

// T22: Connections, Bold, 20pt, Black, leading 24 pt, tracking 0pt
#let font-t22(input_content) = [
  #set par(leading: 24pt)
  #text(
    font: "Arial",
    size: 20pt,
    fill: color_black,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// T23: Connections Cond Bold, Regular, 10pt, Black, leading 12 pt, tracking 0pt
#let font-t23(input_content) = [
  #set par(leading: 12pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_black,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 75%, 
    input_content
  )
]

// T24: Connections Cond Light, Regular, 10pt, White, leading 12 pt, tracking 0pt
#let font-t24(input_content) = [
  #set par(leading: 12pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_white,
    tracking: 0pt,
    weight: "light",
    style: "normal",
    stretch: 75%, 
    input_content
  )
]

// T25: Connections,  Bold, 12pt, Black, leading 14, tracking 0
#let font-t25(input_content) = [
  #set par(leading: 14pt)
  #text(
    font: "Arial",
    size: 12pt,
    fill: color_black,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// T26: Connections Cond Bold,  Regular, 12pt, White, leading 14, tracking 0
#let font-t26(input_content) = [
  #set par(leading: 14pt)
  #text(
    font: "Arial",
    size: 12pt,
    fill: color_white,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 75%, 
    input_content
  )
]

// T27: Connections,  Bold, 8pt, Black, leading 9, tracking 0
#let font-t27(input_content) = [
  #set par(leading: 11pt)
  #text(
    font: "Arial",
    size: 8pt,
    fill: color_black,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// T28: Connections Cond Bold,  Regular, 8pt, Black, leading 9, tracking 0
#let font-t28(input_content) = [
  #set par(leading: 9pt)
  #text(
    font: "Arial",
    size: 8pt,
    fill: color_black,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 75%, 
    input_content
  )
]

// T29: Connections Cond Light,  Regular, 8pt, Black, leading 9, tracking 0
#let font-t29(input_content) = [
  #set par(leading: 9pt)
  #text(
    font: "Arial",
    size: 8pt,
    fill: color_black,
    tracking: 0pt,
    weight: "light",
    style: "normal",
    stretch: 75%, 
    input_content
  )
]

// T30: Connections,  Regular, 12t, White, leading 14, tracking 0
#let font-t30(input_content) = [
  #set par(leading: 14pt)
  #text(
    font: "Arial",
    size: 12pt,
    fill: color_white,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// T31: Connections Light,  Italic, 10pt, Black, leading 12, tracking 0
#let font-t31(input_content) = [
  #set par(leading: 12pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_black,
    tracking: 0pt,
    weight: "light",
    style: "italic",
    stretch: 100%, 
    input_content
  )
]

// T32: Connections Light, Regular, 9pt, Black, leading 10.8 pt, tracking 0pt
#let font-t32(input_content) = [
  #set par(leading: 10.8pt)
  #text(
    font: "Arial",
    size: 9pt,
    fill: color_black,
    tracking: 0pt,
    weight: "light",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// T33: Connections Cond Light, Regular, 9pt, Black, leading 10.8 pt, tracking 0pt
#let font-t33(input_content) = [
  #set par(leading: 10.8pt)
  #text(
    font: "Arial",
    size: 9pt,
    fill: color_black,
    tracking: 0pt,
    weight: "light",
    style: "normal",
    stretch: 75%,
    input_content
  )
]

// T34: Connections Cond Light, Regular, 9.5pt, Black, leading 14 pt, tracking 0pt
#let font-t34(input_content) = [
  #set par(leading: 14pt)
  #text(
    font: "Arial",
    size: 9.5pt,
    fill: color_black,
    tracking: 0pt,
    weight: "light",
    style: "normal",
    stretch: 75%,
    input_content
  )
]

// T35: Connections Cond Light,  Regular, 10pt, Black, leading 12 pt, tracking 0pt
#let font-t35(input_content) = [
  #set par(leading: 12pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_black,
    tracking: 0pt,
    weight: "light",
    style: "normal",
    stretch: 75%,
    input_content
  )
]

// T36: Connections Cond Light,  Regular, 10pt, White, leading 12, tracking 0
#let font-t36(input_content) = [
  #set par(leading: 12pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_white,
    tracking: 0pt,
    weight: "light",
    style: "normal",
    stretch: 75%,
    input_content
  )
]

// T37: Connections,  Bold, 11pt, Black, leading 13.2, tracking 0
#let font-t37(input_content) = [
  #set par(leading: 13.2pt)
  #text(
    font: "Arial",
    size: 11pt,
    fill: color_black,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// T38: Connections Light, 11pt, color equity, leading 13.2, tracking 0
#let font-t38(input_content) = [
  #set par(leading: 13.2pt)
  #text(
    font: "Arial",
    size: 11pt,
    fill: color_equity,
    tracking: 0pt,
    weight: "light",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// T39: Wingdings 2,  Regular, 9.5pt, color fixed income, leading 11.4, tracking 0
#let font-t39(input_content) = [
  #set par(leading: 11.4pt)
  #text(
    font: "Wingdings 2",
    size: 9.5pt,
    fill: color_fixed_income,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    input_content
  )
]

// T40: Wingdings 2,  Regular, 9.5pt, color fixed income, leading 11.4, tracking 0
#let font-t40(input_content) = [
  #set par(leading: 11.4pt)
  #text(
    font: "Wingdings 2",
    size: 9.5pt,
    fill: color_fixed_income,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    input_content
  )
]

// T41: Wingdings 2,  Regular, 9.5pt, color cash, leading 11.4, tracking 0
#let font-t41(input_content) = [
  #set par(leading: 11.4pt)
  #text(
    font: "Wingdings 2",
    size: 9.5pt,
    fill: color_cash,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    input_content
  )
]

// T42: Wingdings 2, Regular, 9.5pt, color alternative investments, leading 11.4, tracking 0
#let font-t42(input_content) = [
  #set par(leading: 11.4pt)
  #text(
    font: "Wingdings 2",
    size: 9.5pt,
    fill: color_alternative_investments,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    input_content
  )
]

// T43: Wingdings 2, Regular, 9.5pt, color dark purple, leading 11.4, tracking 0
#let font-t43(input_content) = [
  #set par(leading: 11.4pt)
  #text(
    font: "Wingdings 2",
    size: 9.5pt,
    fill: color_dark_purple,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    input_content
  )
]

// T44: Wingdings 2, Regular, 9.5pt, color Pantone 280, leading 11.4, tracking 0
#let font-t44(input_content) = [
  #set par(leading: 11.4pt)
  #text(
    font: "Wingdings 2",
    size: 9.5pt,
    fill: color_pantone_280,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    input_content
  )
]

// T45: Wingdings 2,  Regular, 9.5pt, color medium purple, leading 11.4, tracking 0
#let font-t45(input_content) = [
  #set par(leading: 11.4pt)
  #text(
    font: "Wingdings 2",
    size: 9.5pt,
    fill: color_medium_purple,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    input_content
  )
]

// T46: Wingdings 2,  Regular, 9.5pt, color Pantone 293, leading 11.4, tracking 0
#let font-t46(input_content) = [
  #set par(leading: 11.4pt)
  #text(
    font: "Wingdings 2",
    size: 9.5pt,
    fill: color_pantone_293,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    input_content
  )
]

// T47: Wingdings 2,  Regular, 9.5pt, color Pantone 2925, leading 11.4, tracking 0
#let font-t47(input_content) = [
  #set par(leading: 11.4pt)
  #text(
    font: "Wingdings 2",
    size: 9.5pt,
    fill: color_pantone_2925,
    tracking: 0pt,
    weight: "regular",
    input_content
  )
]

// T48: Wingdings 2,  Regular, 9.5pt, color black 60%, leading 11.4, tracking 0
#let font-t48(input_content) = [
  #set par(leading: 11.4pt)
  #text(
    font: "Wingdings 2",
    size: 9.5pt,
    fill: color_black_60,
    tracking: 0pt,
    weight: "regular",
    input_content
  )
]

// T49: Wingdings 2,  Regular, 9.5pt, color black 20%, leading 11.4, tracking 0
#let font-t49(input_content) = [
  #set par(leading: 11.4pt)
  #text(
    font: "Wingdings 2",
    size: 9.5pt,
    fill: color_black_20,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    input_content
  )
]

// T50: Wingdings 2,  Regular, 9.5pt, color black 40%, leading 11.4, tracking 0
#let font-t50(input_content) = [
  #set par(leading: 11.4pt)
  #text(
    font: "Wingdings 2",
    size: 9.5pt,
    fill: color_black_40,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    input_content
  )
]

// T51: Wingdings 2,  Regular, 11pt, color dark blue, leading 13.2, tracking 0
#let font-t51(input_content) = [
  #set par(leading: 13.2pt)
  #text(
    font: "Wingdings 2",
    size: 11pt,
    fill: color_dark_blue,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    input_content
  )
]

// T52: Wingdings 2, Regular, 11pt, color Pantone 285, leading 13.2 pt, tracking 0pt
#let font-t52(input_content) = [
  #set par(leading: 13.2pt)
  #text(
    font: "Wingdings 2",
    size: 11pt,
    fill: color_pantone_285,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    input_content
  )
]

// T53: Connections, Regular, 9pt, color black, leading 10.8 pt, tracking 0pt
#let font-t53(input_content) = [
  #set par(leading: 10.8pt)
  #text(
    font: "Arial",
    size: 9pt,
    fill: color_black,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    stretch: 100%,
    input_content
  )
]

// T54: Connections Cond Light, Regular, 9pt, color white, leading 10.8pt, tracking 0pt
#let font-t54(input_content) = [
  #set par(leading: 10.8pt)
  #text(
    font: "Arial",
    size: 9pt,
    fill: color_white,
    tracking: 0pt,
    weight: "light",
    style: "normal",
    stretch: 100%,
    input_content
  )
]

// T55: Connections Cond Light,  Regular, 9pt, color white, leading 10.8pt, tracking 0pt
#let font-t55(input_content) = [
  #set par(leading: 10.8pt)
  #text(
    font: "Arial",
    size: 9pt,
    fill: color_white,
    tracking: 0pt,
    weight: "light",
    style: "normal",
    stretch: 75%,
    input_content
  )
]

// T56: Wingdings 2,  Regular, 9.5pt, color real assets, leading 11.4pt, tracking 0
#let font-t56(input_content) = [
  #set par(leading: 12pt)
  #text(
    font: "Wingdings 2",
    size: 9.5pt,
    fill: color_real_assets,
    tracking: 0pt,
    weight: "regular",
    input_content
  )
]

// T57: Wingdings 2,  Regular, 9.5pt, color private equity, leading 11.4pt, tracking 0
#let font-t57(input_content) = [
  #set par(leading: 11.4pt)
  #text(
    font: "Wingdings 2",
    size: 9.5pt,
    fill: color_private_equity,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    input_content
  )
]

// T58: Connections Light,  Regular, 16pt, color black, leading 19.2pt, tracking 0
#let font-t58(input_content) = [
  #set par(leading: 19.2pt)
  #text(
    font: "Arial",
    size: 16pt,
    fill: color_black,
    tracking: 0pt,
    weight: "light",
    style: "normal",
    stretch: 100%,
    input_content
  )
]

// T59: Wingdings 2,  Regular, 9.5pt, color Pantone 2224, leading 11.4pt, tracking 0
#let font-t59(input_content) = [
  #set par(leading: 11.4pt)
  #text(
    font: "Wingdings 2",
    size: 9.5pt,
    fill: color_pantone_2224,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    input_content
  )
]

// T60: Connections,  Bold, 9pt, color black, leading 10.8, tracking 0
#let font-t60(input_content) = [
  #set par(leading: 10.8pt)
  #text(
    font: "Arial",
    size: 9pt,
    fill: color_black,
    tracking: 0pt,
    weight: "bold",
    stretch: 100%,
    input_content
  )
]

//Charts and graphs type styles
// C1: Connections, Regular, 12pt, color black, leading 14.4pt, tracking 0pt
#let font-c1(input_content) = [
  #set par(leading: 14.4pt)
  #text(
    font: "Arial",
    size: 12pt,
    fill: color_black,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    stretch: 100%,
    input_content
  )
]

// C2: Connections, Regular, 10pt, color black, leading 12pt, tracking 0pt
#let font-c2(input_content) = [
  #set par(leading: 12pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_black,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// C3: Connections, Bold, 18pt, color black, leading 21.6pt, tracking 0pt
#let font-c3(input_content) = [
  #set par(leading: 21.6pt)
  #text(
    font: "Arial",
    size: 18pt,
    fill: color_black,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// C4: Connections, Regular, 14pt, color black, leading 16.8pt, tracking 0pt
#let font-c4(input_content) = [
  #set par(leading: 16.8pt)
  #text(
    font: "Arial",
    size: 14pt,
    fill: color_black,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// C5: Connections, Bold, 14pt, color black, leading 16.8pt, tracking 0pt
#let font-c5(input_content) = [
  #set par(leading: 16.8pt)
  #text(
    font: "Arial",
    size: 14pt,
    fill: color_black,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// C6: Connections, Bold, 14pt, color white, leading 16.8pt, tracking 0pt
#let font-c6(input_content) = [
  #set par(leading: 16.8pt)
  #text(
    font: "Arial",
    size: 14pt,
    fill: color_white,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// C7: Connections, Regular, 14pt, color white, leading 16.8pt, tracking 0pt
#let font-c7(input_content) = [
  #set par(leading: 16.8pt)
  #text(
    font: "Arial",
    size: 14pt,
    fill: color_white,
    tracking: 0pt,
    weight: "bold",
    stretch: 100%, 
    input_content
  )
]

// C8: Connections, Bold, 10pt, color white, leading 12pt, tracking 0pt
#let font-c8(input_content) = [
  #set par(leading: 12pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_white,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// C9: Connections, Bold, 24pt, color black, leading 28.8pt, tracking 0pt
#let font-c9(input_content) = [
  #set par(leading: 28.8pt)
  #text(
    font: "Arial",
    size: 24pt,
    fill: color_black,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// C10: Connections Light,  Regular, 10pt, color black, leading 12pt, tracking 0
#let font-c10(input_content) = [
  #set par(leading: 12pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_black,
    tracking: 0pt,
    weight: "light",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// C11: Connections,  Bold, 12pt, color black, leading 14.4pt, tracking 0
#let font-c11(input_content) = [
  #set par(leading: 14.4pt)
  #text(
    font: "Arial",
    size: 12pt,
    fill: color_black,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// C12: Connections, Regular, 8pt, color black, leading 10pt, tracking 0pt
#let font-c12(input_content) = [
  #set par(leading: 10pt)
  #text(
    font: "Arial",
    size: 8pt,
    fill: color_black,
    tracking: 0pt,
    weight: "regular",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// C13: Connections, Bold, 12pt, color black, leading 12pt, tracking 0pt
#let font-c13(input_content) = [
  #set par(leading: 12pt)
  #text(
    font: "Arial",
    size: 12pt,
    fill: color_black,
    tracking: 0pt,
    weight: "bold",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// C14: Connections Light, Regular, 9pt, color black, leading 10.8pt, tracking 0pt
#let font-c14(input_content) = [
  #set par(leading: 10.8pt)
  #text(
    font: "Arial",
    size: 9pt,
    fill: color_black,
    tracking: 0pt,
    weight: "light",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// C15: Connections Cond Light,  Regular, 10pt, color black, leading 10pt, tracking 0pt
#let font-c15(input_content) = [
  #set par(leading: 10pt)
  #text(
    font: "Arial",
    size: 10pt,
    fill: color_black,
    tracking: 0pt,
    weight: "light",
    style: "normal",
    stretch: 75%, 
    input_content
  )
]

// C16: Connections Light,  Regular, 12pt, color black, leading 14.4pt, tracking 0pt
#let font-c16(input_content) = [
  #set par(leading: 14.4pt)
  #text(
    font: "Arial",
    size: 12pt,
    fill: color_black,
    tracking: 0pt,
    weight: "light",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// C17: Connections Light,  Regular, 9pt, color black, leading 10pt, tracking 0pt
#let font-c17(input_content) = [
  #set par(leading: 10.8pt)
  #text(
    font: "Connections Light",
    size: 9pt,
    fill: color_black,
    tracking: 0pt,
    weight: "light",
    style: "normal",
    stretch: 100%, 
    input_content
  )
]

// C18: Connections,  Bold, 9pt, color black, leading 10.8pt, tracking 0
//#let font-c18(input_content) = [
//  #set par(leading: 10.8pt)
//  #text(
//    font: "Arial",
//    size: 9pt,
//    fill: color_black,
//    tracking: 0pt,
//    weight: "bold",
//    style: "normal",
//    input_content
//  )
//]

// C19: Connections,  Bold, 22pt, color black, leading 26.4pt, tracking 0
//#let font-c19(input_content) = [
//  #set par(leading: 26.4pt)
//  #text(
//    font: "Arial",
//    size: 22pt,
//    fill: color_black,
//    tracking: 0pt,
//    weight: "bold",
//    style: "normal",
//    input_content
//  )
//]
