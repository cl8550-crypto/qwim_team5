#import "utils_colors.typ": *

// Table row specifications

// R1: background color Pantone 280, row height 0.5208 in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.1875in, right indent 0.1875in, border right 0.5 pt white
#let table_row_r1(input_content) = {
  table.cell(
    fill: color_pantone_280,
    align: left + horizon,
    inset: (
      left: 0.1875in,
      right: 0.1875in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (right: 0.5pt + color_white), 
    [
      #block(
        height: 0.5208in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R2: background color Pantone 293, row height 0.5208 in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.1875in, right indent 0.1875in, border right 0.5 pt white
#let table_row_r2(input_content) = {
  table.cell(
    fill: color_pantone_293,
    align: left + horizon,
    inset: (
      left: 0.1875in,
      right: 0.1875in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (right: 0.5pt + color_white), 
    [
      #block(
        height: 0.5208in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R2 extra: background color Pantone 280, row height 0.195 in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.125 in, right indent 0, border none
#let table_row_r2_extra(input_content) = {
  table.cell(
    fill: color_pantone_280,
    align: left,
    inset: (
      left: 0.125in,
      right: 0.0in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: none,
    [
      #block(
        height: 0.19in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R3: background color Cool Gray, row height 0.5208 in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.1875in, right indent 0.1875in, border none
#let table_row_r3(input_content) = {
  table.cell(
    fill: color_pantone_280,
    align: left + horizon,
    inset: (
      left: 0.1875in,
      right: 0.1875in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: none, 
    [
      #block(
        height: 0.5208in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R4: background color white, row height 1.8125 in, text alignment left, top spacing 0.1875in,
// bottom spacing 0.1875in, left indent 0.1875in, right indent 0.1875in, border 0.25pt right  in "black 40%"
#let table_row_r4(input_content) = {
  table.cell(
    fill: color_white,
    align: left + top,
    inset: (
      left: 0.1875in,
      right: 0.1875in,
      top: 0.1875in,
      bottom: 0.1875in
    ),  
    stroke: (right: 0.25pt + color_black_40), // 0.25pt right border in "black 40%"
    [
      #block(
        height: 1.8125in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R5: background color white, row height 1.8125 in, text alignment left, top spacing 0.1875in,
// bottom spacing 0.1875in, left indent 0.1875in, right indent 0.1875in, border none
#let table_row_r5(input_content) = {
  table.cell(
    fill: color_white,
    align: left + top,
    inset: (
      left: 0.1875in,
      right: 0.1875in,
      top: 0.1875in,
      bottom: 0.1875in
    ),  
    stroke: none,
    [
      #block(
        height: 1.8125in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R6: background color Pantone 280, row height 0.2292in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625 in, right indent 0.0625 in, border none
#let table_row_r6(input_content) = {
  table.cell(
    fill: color_pantone_280,
    align: left + horizon, // left horizontally, centered vertically
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: none,
    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R7: background color white, row height 0.2292in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625in, right indent 0.0625in, border none
#let table_row_r7(input_content) = {
  table.cell(
    fill: color_white,
    align: left + horizon, // left horizontally, centered vertically,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: none,
    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R7 extra: background color white, row height 0.1492in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625in, right indent 0.0625in, border none
#let table_row_r7_extra(input_content) = {
  table.cell(
    fill: color_white,
    align: left + horizon, // left horizontally, centered vertically,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: none,
    [
      #block(
        height: 0.1492in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R8: background color white, row height 0.2292in, text alignment right, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625 in, right indent 0.0625, border none
#let table_row_r8(input_content) = {
  table.cell(
    fill: color_white,
    align: right + horizon, // right horizontally, centered vertically,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: none,
    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R8 extra: background color white, row height 0.1492in, text alignment right, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625 in, right indent 0.0625, border none
#let table_row_r8_extra(input_content) = {
  table.cell(
    fill: color_white,
    align: right + horizon, // right horizontally, centered vertically,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: none,
    [
      #block(
        height: 0.1492in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R8 extra two: background color white, row height 0.1492in, text alignment right, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625 in, right indent 0.0625, border none
#let table_row_r8_extra_two(input_content) = {
  table.cell(
    fill: color_white,
    align: right + horizon, // right horizontally, centered vertically,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: none,
    [
      #block(
        height: 0.1892in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R9: background color black 10%, row height 0.2292in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625in, right indent 0.0625in, border none
#let table_row_r9(input_content) = {
  table.cell(
    fill: color_black_10,
    align: left + horizon, // left horizontally, centered vertically,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: none,
    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R9 extra: background color black 10%, row height 0.1492in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625in, right indent 0.0625in, border none
#let table_row_r9_extra(input_content) = {
  table.cell(
    fill: color_black_10,
    align: left + horizon, // left horizontally, centered vertically,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: none,
    [
      #block(
        height: 0.1492in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R10: background color black 10%, row height 0.2292in, text alignment right, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625in, right indent 0.0625in, border none
#let table_row_r10(input_content) = {
  table.cell(
    fill: color_black_10,
    align: right + horizon, // right horizontally, centered vertically,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: none,
    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R10 extra: background color black 10%, row height 0.1492in, text alignment right, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625in, right indent 0.0625in, border none
#let table_row_r10_extra(input_content) = {
  table.cell(
    fill: color_black_10,
    align: right + horizon, // right horizontally, centered vertically,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: none,
    [
      #block(
        height: 0.1492in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R10 extra two: background color black 10%, row height 0.1892in, text alignment right, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625in, right indent 0.0625in, border none
#let table_row_r10_extra_two(input_content) = {
  table.cell(
    fill: color_black_10,
    align: right + horizon, // right horizontally, centered vertically,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: none,
    [
      #block(
        height: 0.1892in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R11: background color black 10%, row height 0.2292in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625in, right indent 0.0625in, border bottom 1pt black 40%
#let table_row_r11(input_content) = {
  table.cell(
    fill: color_black_10,
    align: left + horizon, // left horizontally, centered vertically,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (bottom: 1pt + color_black_40), // 1pt bottom border in "black 40%",
    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R12: background color black 10%, row height 0.2292in, text alignment right, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625in, right indent 0.0625in, border bottom 1pt black 40%
#let table_row_r12(input_content) = {
  table.cell(
    fill: color_black_10,
    align: right + horizon, // right horizontally, centered vertically,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (bottom: 1pt + color_black_40), // 1pt bottom border in "black 40%",
    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
} 

// R13: background color Pantone 2925 20%, row height 0.2292in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625 in, right indent 0.0625, border none
#let table_row_r13(input_content) = {
  table.cell(
    fill: color_pantone_2925_20pct,
    align: left + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: none,
    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R14: background color Pantone 2925 20%, row height 0.2292in, text alignment right, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625 in, right indent 0.0625, border none
#let table_row_r14(input_content) = {
  table.cell(
    fill: color_pantone_2925_20pct,
    align: right + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: none,
    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R15: background color Pantone 280, row height 0.5208in, text alignment left, top spacing 0.125in,
// bottom spacing 0.125in, left indent 0.0625 in, right indent 0.0625, border none
#let table_row_r15(input_content) = {
  table.cell(
    fill: color_pantone_280,
    align: left + bottom,
    inset: (
      left: 0.125in,
      right: 0.125in,
      top: 0.0625in,
      bottom: 0.0625in
    ),  
    stroke: none,
    [
      #block(
        height: 0.5208in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R16: background color Pantone 280, row height 0.5208in, text alignment right, top spacing 0.125in,
// bottom spacing 0.125in, left indent 0.0625 in, right indent 0.0625, border none
#let table_row_r16(input_content) = {
  table.cell(
    fill: color_pantone_280,
    align: right + bottom,
    inset: (
      left: 0.125in,
      right: 0.125in,
      top: 0.0625in,
      bottom: 0.0625in
    ),  
    stroke: none,
    [
      #block(
        height: 0.5208in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R17: background color white, row height 0.3958in, text alignment left, top spacing 0.0625in,
// bottom spacing 0.0625in, left indent 0.0625 in, right indent 0.0625, border none
#let table_row_r17(input_content) = {
  table.cell(
    fill: color_white,
    align: left + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.0625in,
      bottom: 0.0625in
    ),  
    stroke: none,
    [
      #block(
        height: 0.3958in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R18: background color white, row height 0.3958in, text alignment right, top spacing 0.0625in,
// bottom spacing 0.0625in, left indent 0.0625 in, right indent 0.0625, border none
#let table_row_r18(input_content) = {
  table.cell(
    fill: color_white,
    align: right + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.0625in,
      bottom: 0.0625in
    ),  
    stroke: none,
    [
      #block(
        height: 0.3958in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R19: background color white, row height 0.2292in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625in, right indent 0.0625in, border 1pt bottom in "black 40%"
#let table_row_r19(input_content) = {
  table.cell(
    fill: color_white,
    align: left + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (bottom: 1pt + color_black_40), // 1pt bottom border in "black 40%"
    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R20: background color white, row height 0.2292in, text alignment right, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625in, right indent 0.0625in, border 1pt bottom in "black 40%"
#let table_row_r20(input_content) = {
  table.cell(
    fill: color_white,
    align: right + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (bottom: 1pt + color_black_40), // 1pt bottom border in "black 40%"
    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R21: background color Pantone 2925 20%, row height 0.2292in, text alignment left, top spacing 0.0625in,
// bottom spacing 0.0625in, left indent 0.0625in, right indent 0.0625in, border none
#let table_row_r21(input_content) = {
  table.cell(
    fill: color_pantone_2925_20pct,
    align: left + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.0625in,
      bottom: 0.0625in
    ),  
    stroke: none,
    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R22: background color Pantone 2925 20%, row height 0.2292in, text alignment right, top spacing 0.0625in,
// bottom spacing 0.0625in, left indent 0.0625in, right indent 0.0625in, border none
#let table_row_r22(input_content) = {
  table.cell(
    fill: color_pantone_2925_20pct,
    align: right + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.0625in,
      bottom: 0.0625in
    ),  
    stroke: none,
    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R23: background color black 10%, row height 0.2292in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625in, right indent 0.0625in, border Top, Left, Bottom 1pt Blue 90
#let table_row_r23(input_content) = {
  table.cell(
    fill: color_black_10,
    align: left + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    1pt + color_blue_90,
      left:   1pt + color_blue_90,
      bottom: 1pt + color_blue_90
    ),

    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R24: background color black 10%, row height 0.2292in, text alignment right, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625in, right indent 0.0625in, border Top, Bottom 1pt Blue 90
#let table_row_r24(input_content) = {
  table.cell(
    fill: color_black_10,
    align: right + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    1pt + color_blue_90,
      bottom: 1pt + color_blue_90
    ),

    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R25: background color black 10%, row height 0.2292in, text alignment right, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625in, right indent 0.0625in, border Top, right, Bottom 1pt Blue 90
#let table_row_r25(input_content) = {
  table.cell(
    fill: color_black_10,
    align: right + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    1pt + color_blue_90,
      right:    1pt + color_blue_90,
      bottom: 1pt + color_blue_90
    ),

    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R26: background color Pantone 2925 20%, row height 0.2292in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625in, right indent 0.0625in, border Top, left 1pt Blue 90
#let table_row_r26(input_content) = {
  table.cell(
    fill: color_pantone_2925_20pct,
    align: left + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    1pt + color_blue_90,
      left:    1pt + color_blue_90,
      bottom:    1pt + color_blue_90
    ),

    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R27: background color Pantone 2925 20%, row height 0.2292in, text alignment right, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625in, right indent 0.0625in, border Top 1pt Blue 90
#let table_row_r27(input_content) = {
  table.cell(
    fill: color_pantone_2925_20pct,
    align: right + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    1pt + color_blue_90,
      bottom: 1pt + color_blue_90
    ),

    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R28: background color Pantone 2925 20%, row height 0.2292in, text alignment right, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625in, right indent 0.0625in, border Top, right 1pt Blue 90
#let table_row_r28(input_content) = {
  table.cell(
    fill: color_pantone_2925_20pct,
    align: right + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    1pt + color_blue_90,
      right:  1pt + color_blue_90,
      bottom:  1pt + color_blue_90
    ),

    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R29: background color white, row height 0.2292in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625in, right indent 0.0625in, border Top, left 1pt Blue 90
#let table_row_r29(input_content) = {
  table.cell(
    fill: color_white,
    align: left + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:   1pt + color_blue_90,
      left:  1pt + color_blue_90
    ),

    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R30: background color white, row height 0.2292in, text alignment right, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625in, right indent 0.0625in, border Top 1pt Blue 90
#let table_row_r30(input_content) = {
  table.cell(
    fill: color_white,
    align: right + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    1pt + color_blue_90
    ),

    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R31: background color white, row height 0.2292in, text alignment right, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625in, right indent 0.0625in, border Top, right 1pt Blue 90
#let table_row_r31(input_content) = {
  table.cell(
    fill: color_white,
    align: right + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    1pt + color_blue_90,
      right:  1pt + color_blue_90
    ),

    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R32: background color Pantone 2925 20%, row height 0.2292in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625in, right indent 0.0625in, border left 1pt Blue 90
#let table_row_r32(input_content) = {
  table.cell(
    fill: color_pantone_2925_20pct,
    align: left + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      left:    1pt + color_blue_90
    ),

    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R33: background color Pantone 2925 20%, row height 0.2292in, text alignment right, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625in, right indent 0.0625in, border right 1pt Blue 90
#let table_row_r33(input_content) = {
  table.cell(
    fill: color_pantone_2925_20pct,
    align: right + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      right:  1pt + color_blue_90
    ),

    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R34: background color white, row height 0.2292in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625in, right indent 0.0625in, border left, bottom 1pt Blue 90
#let table_row_r34(input_content) = {
  table.cell(
    fill: color_white,
    align: left + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      left:   1pt + color_blue_90,
      bottom: 1pt + color_blue_90
    ),

    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R35: background color white, row height 0.2292in, text alignment right, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625in, right indent 0.0625in, border bottom 1pt Blue 90
#let table_row_r35(input_content) = {
  table.cell(
    fill: color_white,
    align: right + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      bottom:    1pt + color_blue_90
    ),

    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R36: background color white, row height 0.2292in, text alignment right, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.0625in, right indent 0.0625in, border bottom, right 1pt Blue 90
#let table_row_r36(input_content) = {
  table.cell(
    fill: color_white,
    align: right + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      bottom: 1pt + color_blue_90,
      right:  1pt + color_blue_90
    ),

    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R37: background color Pantone 293, row height 0.2292in, text alignment left, top spacing 0.0625in,
// bottom spacing 0.0625in, left indent 0.0625in, right indent 0.0625in, border none
#let table_row_r37(input_content) = {
  table.cell(
    fill: color_pantone_293,
    align: left + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.0625in,
      bottom: 0.0625in
    ),  
    stroke: none,

    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R38: background color Pantone 293, row height 0.2292in, text alignment right, top spacing 0.0625in,
// bottom spacing 0.0625in, left indent 0.0625in, right indent 0.0625in, border none
#let table_row_r38(input_content) = {
  table.cell(
    fill: color_pantone_293,
    align: right + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.0625in,
      bottom: 0.0625in
    ),  
    stroke: none,

    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R39: background color Pantone 293, row height 0.3958in, text alignment left, top spacing 0.0625in,
// bottom spacing 0.0625in, left indent 0.0625in, right indent 0.0625in, border none
#let table_row_r39(input_content) = {
  table.cell(
    fill: color_pantone_293,
    align: left + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.0625in,
      bottom: 0.0625in
    ),  
    stroke: none,

    [
      #block(
        height: 0.3958in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R39 extra: background color Pantone 280, row height 0.3958in, text alignment left, top spacing 0.0625in,
// bottom spacing 0.0625in, left indent 0.0625in, right indent 0.0625in, border none
#let table_row_r39_extra(input_content) = {
  table.cell(
    fill: color_pantone_280,
    align: left + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.0625in,
      bottom: 0.0625in
    ),  
    stroke: none,

    [
      #block(
        height: 0.3958in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R39 extra narrow: background color Pantone 280, row height 0.2292in, text alignment left, top spacing 0.0625in,
// bottom spacing 0.0625in, left indent 0.0625in, right indent 0.0625in, border none
#let table_row_r39_extra_narrow(input_content) = {
  table.cell(
    fill: color_pantone_280,
    align: left + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.0625in,
      bottom: 0.0625in
    ),  
    stroke: none,

    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R40: background color Pantone 293, row height 0.3958in, text alignment right, top spacing 0.0625in,
// bottom spacing 0.0625in, left indent 0.0625in, right indent 0.0625in, border none
#let table_row_r40(input_content) = {
  table.cell(
    fill: color_pantone_293,
    align: right + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.0625in,
      bottom: 0.0625in
    ),  
    stroke: none,

    [
      #block(
        height: 0.3958in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R40 extra: background color Pantone 280, row height 0.3958in, text alignment right, top spacing 0.0625in,
// bottom spacing 0.0625in, left indent 0.0625in, right indent 0.0625in, border none
#let table_row_r40_extra(input_content) = {
  table.cell(
    fill: color_pantone_280,
    align: right + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.0625in,
      bottom: 0.0625in
    ),  
    stroke: none,

    [
      #block(
        height: 0.3958in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R40 extra narrow: background color Pantone 280, row height 0.2292in, text alignment right, top spacing 0.0625in,
// bottom spacing 0.0625in, left indent 0.0625in, right indent 0.0625in, border none
#let table_row_r40_extra_narrow(input_content) = {
  table.cell(
    fill: color_pantone_280,
    align: right + horizon,
    inset: (
      left: 0.0625in,
      right: 0.0625in,
      top: 0.0625in,
      bottom: 0.0625in
    ),  
    stroke: none,

    [
      #block(
        height: 0.2292in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R41: background color white, row height 0.4308in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0, right indent 0.0625in, border top 0.25pt color black 40%
#let table_row_r41(input_content) = {
  table.cell(
    fill: color_white,
    align: left + top,
    inset: (
      left: 0.0in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    0.25pt + color_black_40
    ),

    [
      #block(
        height: 0.4308in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R41 Extra: background color white, row height 0.4308in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0, right indent 0.0625in, border top 0.25pt color black 40%
#let table_row_r41_extra(input_content) = {
  table.cell(
    fill: color_white,
    align: left + horizon,
    inset: (
      left: 0.0in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:  0.25pt + color_black_40
    ),

    [
      #block(
        height: 0.4308in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R42: background color white, row height 0.4308in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.125in, right indent 0.0625in, border top 0.25pt color black 40%
#let table_row_r42(input_content) = {
  table.cell(
    fill: color_white,
    align: left + top,
    inset: (
      left: 0.125in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    0.25pt + color_black_40
    ),

    [
      #block(
        height: 0.4308in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R42 Extra: background color white, row height 0.4308in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.125in, right indent 0.0625in, border top 0.25pt color black 40%
#let table_row_r42_extra(input_content) = {
  table.cell(
    fill: color_white,
    align: left + horizon,
    inset: (
      left: 0.125in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    0.25pt + color_black_40
    ),

    [
      #block(
        height: 0.4308in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R43: background color white, row height 0.5975in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0, right indent 0.0625in, border top 0.25pt color black 40%
#let table_row_r43(input_content) = {
  table.cell(
    fill: color_white,
    align: left + top,
    inset: (
      left: 0.0in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    0.25pt + color_black_40
    ),

    [
      #block(
        height: 0.5975in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R43 Extra: background color white, row height 0.5975in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0, right indent 0.0625in, border top 0.25pt color black 40%
#let table_row_r43_extra(input_content) = {
  table.cell(
    fill: color_white,
    align: left + horizon,
    inset: (
      left: 0.0in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    0.25pt + color_black_40
    ),

    [
      #block(
        height: 0.5975in,
        width: 100%,
        breakable: false,
        [
          #set par(leading:0.25em)
//          #set par(leading:0.25em, spacing:0pt)
          #input_content
        ]
      )
    ]
  )
}

// R44: background color white, row height 0.5975in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.125in, right indent 0.0625in, border top 0.25pt color black 40%
#let table_row_r44(input_content) = {
  table.cell(
    fill: color_white,
    align: left + top,
    inset: (
      left: 0.125in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    0.25pt + color_black_40
    ),

    [
      #block(
        height: 0.5975in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R44 extra: background color white, row height 0.5975in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.125in, right indent 0.0625in, border top 0.25pt color black 40%
#let table_row_r44_extra(input_content) = {
  table.cell(
    fill: color_white,
    align: left + horizon,
    inset: (
      left: 0.125in,
      right: 0.0625in,
      top: 0.06in,
      bottom: 0.06in
    ),  
    stroke: (
      top:    0.25pt + color_black_40
    ),

    [
      #block(
        height: 0.5975in,
        width: 100%,
        breakable: false,
        [
          #set par(leading:0.25em)
//          #set par(leading:0.25em, spacing:0pt)
          #input_content
        ]
      )
    ]
  )
}

// R45: background color white, row height 0.2642in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0, right indent 0.0625in, border top 0.25pt color black 40%
#let table_row_r45(input_content) = {
  table.cell(
    fill: color_white,
    align: left + top,
    inset: (
      left: 0.0in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    0.25pt + color_black_40
    ),

    [
      #block(
        height: 0.2642in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R45 Extra: background color white, row height 0.2642in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0, right indent 0.0625in, border top 0.25pt color black 40%
#let table_row_r45_extra(input_content) = {
  table.cell(
    fill: color_white,
    align: left + horizon,
    inset: (
      left: 0.0in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    0.25pt + color_black_40
    ),

    [
      #block(
        height: 0.2642in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R46: background color white, row height 0.2642in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.125in, right indent 0.0625in, border top 0.25pt color black 40%
#let table_row_r46(input_content) = {
  table.cell(
    fill: color_white,
    align: left + top,
    inset: (
      left: 0.125in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    0.25pt + color_black_40
    ),

    [
      #block(
        height: 0.2642in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R46 Extra: background color white, row height 0.2642in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.125in, right indent 0.0625in, border top 0.25pt color black 40%
#let table_row_r46_extra(input_content) = {
  table.cell(
    fill: color_white,
    align: left + horizon,
    inset: (
      left: 0.125in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    0.25pt + color_black_40
    ),

    [
      #block(
        height: 0.2642in,
        width: 100%,
        breakable: false,
        [
          #set par(leading:0.25em)
 //         #set par(leading:0.25em, spacing:0pt)
          #input_content
        ]
      )
    ]
  )
}

// R47: background color white, row height 0.4308in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0, right indent 0.0625in, border top bottom 0.25pt color black 40%
#let table_row_r47(input_content) = {
  table.cell(
    fill: color_white,
    align: left + top,
    inset: (
      left: 0.0in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    0.25pt + color_black_40,
      bottom: 0.25pt + color_black_40
    ),

    [
      #block(
        height: 0.4308in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R47 extra: background color white, row height 0.4308in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0, right indent 0.0625in, border top bottom 0.25pt color black 40%
#let table_row_r47_extra(input_content) = {
  table.cell(
    fill: color_white,
    align: left + horizon,
    inset: (
      left: 0.0in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    0.25pt + color_black_40,
      bottom: 0.25pt + color_black_40
    ),

    [
      #block(
        height: 0.4308in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R48: background color white, row height 0.4308in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.125in, right indent 0.0625in, border top bottom 0.25pt color black 40%
#let table_row_r48(input_content) = {
  table.cell(
    fill: color_white,
    align: left + top,
    inset: (
      left: 0.125in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    0.25pt + color_black_40,
      bottom: 0.25pt + color_black_40
    ),

    [
      #block(
        height: 0.4308in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R48 extra: background color white, row height 0.4308in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.125in, right indent 0.0625in, border top bottom 0.25pt color black 40%
#let table_row_r48_extra(input_content) = {
  table.cell(
    fill: color_white,
    align: left + horizon,
    inset: (
      left: 0.125in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    0.25pt + color_black_40,
      bottom:    0.25pt + color_black_40
    ),

    [
      #block(
        height: 0.4308in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R49: background color white, row height 0.5975in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0, right indent 0.0625in, border top bottom 0.25pt color black 40%
#let table_row_r49(input_content) = {
  table.cell(
    fill: color_white,
    align: left + top,
    inset: (
      left: 0.0in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    0.25pt + color_black_40,
      bottom: 0.25pt + color_black_40
    ),

    [
      #block(
        height: 0.5975in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R49 extra: background color white, row height 0.5975in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0, right indent 0.0625in, border top bottom 0.25pt color black 40%
#let table_row_r49_extra(input_content) = {
  table.cell(
    fill: color_white,
    align: left + horizon,
    inset: (
      left: 0.0in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    0.25pt + color_black_40,
      bottom: 0.25pt + color_black_40
    ),

    [
      #block(
        height: 0.5975in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R50: background color white, row height 0.5975in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.125in, right indent 0.0625in, border top bottom 0.25pt color black 40%
#let table_row_r50(input_content) = {
  table.cell(
    fill: color_white,
    align: left + top,
    inset: (
      left: 0.125in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    0.25pt + color_black_40,
      bottom: 0.25pt + color_black_40
    ),

    [
      #block(
        height: 0.5975in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}

// R50 extra: background color white, row height 0.5975in, text alignment left, top spacing 0.03in,
// bottom spacing 0.03in, left indent 0.125in, right indent 0.0625in, border top bottom 0.25pt color black 40%
#let table_row_r50_extra(input_content) = {
  table.cell(
    fill: color_white,
    align: left + horizon,
    inset: (
      left: 0.125in,
      right: 0.0625in,
      top: 0.03in,
      bottom: 0.03in
    ),  
    stroke: (
      top:    0.25pt + color_black_40,
      bottom: 0.25pt + color_black_40
    ),

    [
      #block(
        height: 0.5975in,
        width: 100%,
        breakable: false,
        [#input_content]
      )
    ]
  )
}