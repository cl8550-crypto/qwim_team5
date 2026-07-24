
#import "utils_fonts.typ": *
#import "utils_colors.typ": *

#let default_footer_text = "Powered by QWIM Team"
#let footer_text_source_AAPCA_ISG = "Source: QWIM Team"
#let default_notes_text = "Notes: ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
#let notes_important_info = "Notes: icta sunt explicabo, nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos saepe."

#let get_current_date() = {
  let today = datetime.today()
  let month_names = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")
  let month_name = month_names.at(today.month() - 1)
  month_name + " " + str(today.day()) + ", " + str(today.year())
}



#let set_page_footer(footer_text) = {
  // Footer text - 0.25" from bottom edge (page height is 8.27" for A4 landscape)
  place(
    top + left,
    dx: 0.5in,
    dy: 8.02in,  // 8.27" - 0.25" = 8.02"
    text(font: "Arial", size: 10pt, weight: "bold", fill: black)[
      #footer_text
    ]
  )
  
  // Page number - bottom right corner
  place(
    top + right,
    dx: -0.5in,
    dy: 8.02in,
    text(font: "Arial", size: 10pt, fill: black)[
      Page #context counter(page).display()
    ]
  )
}



#let set_page_footer_and_notes(footer_text, notes_text, dy_footer:7.82in, dy_notes:8.02in, dy_page_number:8.02in) = {
  // Footer text - 0.25" from bottom edge (page height is 8.27" for A4 landscape)
  place(
    top + left,
    dx: 0.5in,
    dy: dy_footer, // 7.82in,  
    text(font: "Arial", size: 10pt, weight: "bold", fill: black)[
      #footer_text
    ]
  )
  
  // Notes text below footer
  place(
    top + left,
    dx: 0.5in,
    dy: dy_notes, // 8.02in,
    text(font: "Arial", size: 8.5pt, fill: black)[
      #notes_text
    ]
  )
  
  // Page number - bottom right corner
  place(
    top + right,
    dx: -0.5in,
    dy: dy_page_number, // 8.02in,  // Align with notes text
    text(font: "Arial", size: 10pt, fill: black)[
      Page #context counter(page).display()
    ]
  )
}


#let set_page_notes_and_footer(notes_text:" ", footer_text:" ", dy_notes:7.82in, dy_footer:8.02in,  dy_page_number:8.02in) = {

  // Notes text above footer
  place(
    top + left,
    dx: 0.5in,
    dy: dy_notes, 
    text(font: "Arial", size: 8.5pt, fill: black)[
      #notes_text
    ]
  )
  
  place(
    top + left,
    dx: 0.5in,
    dy: dy_footer,   
    text(font: "Arial", size: 10pt, weight: "bold", fill: black)[
      #footer_text
    ]
  )
  
  // Page number - bottom right corner
  place(
    top + right,
    dx: -0.5in,
    dy: dy_page_number, 
    text(font: "Arial", size: 10pt, fill: black)[
      Page #context counter(page).display()
    ]
  )
}


#let set_page_source_notes_and_footer(source_text: " ", notes_text:" ", footer_text:" ", 
    dy_source:7.62in, dy_notes:7.82in, dy_footer:8.02in,  dy_page_number:8.02in) = {

  // source text above notes
  place(
    top + left,
    dx: 0.5in,
    dy: dy_source, 
    text(font: "Arial", size: 8.5pt, fill: black)[
      #source_text
    ]
  )
  
  // Notes text above footer
  place(
    top + left,
    dx: 0.5in,
    dy: dy_notes, 
    text(font: "Arial", size: 8.5pt, fill: black)[
      #notes_text
    ]
  )
  
  place(
    top + left,
    dx: 0.5in,
    dy: dy_footer,   
    text(font: "Arial", size: 10pt, weight: "bold", fill: black)[
      #footer_text
    ]
  )
  
  // Page number - bottom right corner
  place(
    top + right,
    dx: -0.5in,
    dy: dy_page_number, 
    text(font: "Arial", size: 10pt, fill: black)[
      Page #context counter(page).display()
    ]
  )
}


#let set_page_footer_and_notes_for_surplus(footer_text, notes_text) = {
  place(
    top + left,
    dx: 0.5in,
    dy: 7.62in,  // Higher position to accommodate notes below
    text(font: "Arial", size: 10pt, weight: "bold", fill: black)[
      #footer_text
    ]
  )
  
  // Notes text below footer
  place(
    top + left,
    dx: 0.5in,
    dy: 7.82in,  // 0.2" below footer text
    text(font: "Arial", size: 8.5pt, fill: black)[
      #notes_text
    ]
  )
  
  // Page number - bottom right corner
  place(
    top + right,
    dx: -0.5in,
    dy: 8.02in,  // Align with notes text
    text(font: "Arial", size: 10pt, fill: black)[
      Page #context counter(page).display()
    ]
  )
}


#let set_page_header(header_text) = {
  // Header text:  at 0.6059" from top, 0.5" from left
  place(
    top + left,
    dx: 0.5in,
    dy: 0.6059in,
    font-g1[#header_text]
  )
}


#let set_report_header_investor(header_text) = {
  place(
    top + left,
    dx: 0.5in,
    dy: 3.17in,
    font-g10[#header_text]
  )
}


#let get_first_name(full_name) = {
  let parts = full_name.split(" ")
  parts.at(0)
}


#let set_report_title_page_financial_advisor_name(input_text) = {
  place(
    top + left,
    dx: 0.5in,
    dy: 6.50in,
    font-g6[#input_text]
  )
}


#let set_report_title_page_financial_advisor_team(input_text) = {
  place(
    top + left,
    dx: 0.5in,
    dy: 6.70in,
    font-g6[#input_text]
  )
}


#let set_report_title_page_financial_advisor(input_text) = {
  place(
    top + left,
    dx: 0.5in,
    dy: 6.90in,
    font-g7[#input_text]
  )
}


#let set_report_title_page_financial_advisor_firm(input_text) = {
  place(
    top + left,
    dx: 0.5in,
    dy: 7.10in,
    font-g7[#input_text]
  )
}


#let set_report_title_page_financial_advisor_phone(input_text) = {
  place(
    top + left,
    dx: 0.5in,
    dy: 7.30in,
    font-g6[#input_text]
  )
}


#let set_report_title_page_financial_advisor_email(input_text) = {
  place(
    top + left,
    dx: 0.5in,
    dy: 7.50in,
    font-g6[#input_text]
  )
}


#let convert_string_dollars_to_number(value_string) = {
  let string_as_number = str(value_string).trim()
      // normalize Unicode minus to ASCII minus (optional but robust)
  let string_as_number = string_as_number.replace("−", "-")
      // remove $ and commas anywhere in the string
  let string_as_number = string_as_number.replace(regex("[$,]"), "")

  int(string_as_number)
}


#let display_negative_value(
  item_idx,
  color_fill_for_negative_value,
) = {

  let item_idx_as_number = convert_string_dollars_to_number(str(item_idx))
      
  if item_idx_as_number < 0 {
    text(fill: color_fill_for_negative_value)[#str(item_idx)]
  } else {
    [#str(item_idx)]
  }
}
