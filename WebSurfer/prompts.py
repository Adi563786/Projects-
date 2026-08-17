# def get_page_purpose_prompt(
#     task,
#     url,
#     title,
#     elements,
#     relevant_frames,
#     previous_page_tasks=None,
# ):
#     previous_page_tasks = previous_page_tasks or []

#     return f"""
# You determine the NEXT LOGICAL STEP needed to progress the MAIN TASK on the current page.

# MAIN TASK:
# {task}

# PREVIOUS COMPLETED PAGE TASKS:
# {previous_page_tasks}

# CURRENT PAGE:
# URL: {url}
# Title: {title}

# PAGE ELEMENTS:
# {elements}

# Your job:
# Identify what should be done NEXT on this page to make the most progress toward MAIN TASK.

# GENERAL RULES:

# 1. Use only information, controls, and content present in PAGE ELEMENTS.

# 2. Prefer completing the task on the current page.
#    Do not navigate away if the required information or action is already available.

# 3. Do not repeat anything already completed in PREVIOUS COMPLETED PAGE TASKS.

# 4. Describe the COMPLETE logical step, not an isolated UI action.
#    The sentence should explain the intended outcome.

# 5. Preserve exact spelling, capitalization, numbers, names, entities, and values
#    from MAIN TASK whenever something must be entered or searched.

# 6. Never invent:
#    - buttons
#    - links
#    - form fields
#    - search boxes
#    - values
#    - page content
#    - results
#    - URLs

# 7. If the MAIN TASK is already satisfied by information on the current page,
#    instruct extracting/reading the required information instead of performing another action.

# 8. If the required control or information is NOT present on this page,
#    describe the next logical navigation step using an available link or control.

# SEARCHING:

# 9. If the task requires searching and a search input is available but has not
#    been used for the required query, describe the COMPLETE search operation.

#    Example:
#    "Enter "wireless headphones under $100" in the search box and submit the search."

#    Do NOT say:
#    "Click the search button."

# 10. If the search box already contains the required query, do not enter it again.
#     Instruct submitting the search if needed.

# 11. If relevant search results are already displayed, do not search again.
#     Instruct opening the first relevant result.

# 12. If multiple results are visible, choose the result that best matches the
#     entity, product, person, or information requested by MAIN TASK.

# 13. Do not open advertisements, sponsored results, or unrelated results when
#     an appropriate organic result is available.

# FORM FILLING:

# 14. If MAIN TASK requires filling a form, identify the fields that need values
#     and describe filling the required fields with the exact requested values.

#     Example:
#     "Fill the name field with "John Smith", email with "john@example.com", and
#     phone with "5551234567"."

# 15. If only one field remains to be completed, describe only that remaining step.

#     Example:
#     "Enter "New York" in the destination field."

# 16. If a dropdown/select is required and the requested option is present,
#     instruct selecting that option.

#     Example:
#     "Select "United States" from the country dropdown."

# 17. If a checkbox is required and it is currently unchecked, instruct checking it.

#     Example:
#     "Check the "I agree to the terms" checkbox."

# 18. Do not change fields that are already correctly filled.

# 19. Do not submit a form until all required information needed for MAIN TASK
#     has been entered.

# 20. Once the form is correctly completed and a submit/continue button exists,
#     instruct submitting/continuing the form.

#     Example:
#     "Submit the completed registration form."

# GETTING INFORMATION / TEXT:

# 21. If MAIN TASK asks for information that is already present on the page,
#     instruct extracting that information.

#     Example:
#     "Read and extract the product's current price and availability."

# 22. If MAIN TASK asks for multiple pieces of information, extract all relevant
#     information that is currently available.

#     Example:
#     "Extract the article's title, author, publication date, and main text."

# 23. Do not navigate to another page when the requested information is already
#     available on the current page.

# 24. If only part of the requested information is available, extract the
#     available information and continue to the next logical page/action for
#     the missing information.

# NAVIGATION:

# 25. If MAIN TASK requires opening another page and an appropriate link is
#     present, instruct opening that link.

#     Example:
#     "Open the product page for Sony WH-1000XM5."

# 26. If the destination page is already open, do not click links that merely
#     reopen the same page.

# 27. If the required destination is not available through the current page,
#     describe the most logical available navigation step.

# SELECTION:

# 28. If MAIN TASK requires choosing an item, use visible information to identify
#     the best matching option.

#     Example:
#     "Select the "Large" size and "Black" color."

# 29. Do not select an option merely because it is the first option if MAIN TASK
#     specifies another value.

# PAGINATION / MORE RESULTS:

# 30. If the required information is not present in the current results and a
#     next-page, load-more, or pagination control exists, instruct using it.

#     Example:
#     "Open the next results page to continue looking for the requested product."

# STOPPING:

# 31. If MAIN TASK has already been completed on the current page, instruct
#     extracting the final result or state that the required information/action
#     is complete.

# 32. Do not perform unnecessary actions after the MAIN TASK is satisfied.

# OUTPUT:

# Return ONLY ONE short sentence describing the NEXT logical step on this page.

# Do not explain your reasoning.
# Do not provide alternatives.
# Do not use bullet points.
# Do not mention these rules.

# Examples:

# MAIN TASK:
# "Find the price of the iPhone 16 Pro."

# PAGE:
# Search box and product results are visible.

# OUTPUT:
# "Open the first relevant iPhone 16 Pro result to find its price."

# MAIN TASK:
# "Search for Python courses."

# PAGE:
# Search input and Search button are visible, query has not been entered.

# OUTPUT:
# "Enter "Python courses" in the search box and submit the search."

# MAIN TASK:
# "Book a flight from Delhi to Mumbai."

# PAGE:
# Origin, destination, date, and Search Flights controls are visible.

# OUTPUT:
# "Fill the flight search form with Delhi as the origin, Mumbai as the destination, the requested date, and submit the search."

# MAIN TASK:
# "Get the phone number of the company."

# PAGE:
# The company's phone number is visible.

# OUTPUT:
# "Read and extract the company's phone number."

# MAIN TASK:
# "Create an account using John Smith and john@example.com."

# PAGE:
# Name and email fields plus a Create Account button are visible.

# OUTPUT:
# "Fill the name with "John Smith" and email with "john@example.com", then create the account."

# MAIN TASK:
# "Find the return policy for this product."

# PAGE:
# A product page with a visible "Return Policy" link exists.

# OUTPUT:
# "Open the visible Return Policy link to find the product's return policy."

# MAIN TASK:
# "Find the cheapest laptop under $800."

# PAGE:
# Several laptop search results with prices are visible.

# OUTPUT:
# "Compare the visible laptop results and identify the cheapest one priced below $800."

# MAIN TASK:
# "Find the address of the restaurant."

# PAGE:
# The restaurant address is already visible.

# OUTPUT:
# "Read and extract the restaurant's address."

# MAIN TASK:
# "Find the requested item in the search results."

# PAGE:
# The current results do not contain it, but a Next button is visible.

# OUTPUT:
# "Open the next results page to continue searching for the requested item."

# Now determine the next logical step.
# """.strip()

def get_page_purpose_prompt(
    task,
    url,
    title,
    elements,
    previous_page_tasks=None,
    reason_why_task_is_not_completed="",
    forms=""
):
    previous_page_tasks = previous_page_tasks or []

    return f"""
You determine the NEXT LOGICAL PAGE TASK that best advances the MAIN TASK.

MAIN TASK:
{task}

COMPLETED PAGE TASKS:
{previous_page_tasks}

WHY MAIN TASK IS STILL INCOMPLETE:
{reason_why_task_is_not_completed or "Not provided"}

CURRENT PAGE:
URL: {url}
Title: {title}



FORMS:
{forms}

ELEMENTS:
{elements}

CORE RULES:

1. MAIN TASK defines the final goal.

2. If WHY MAIN TASK IS STILL INCOMPLETE is provided, treat it as the
   HIGHEST-PRIORITY continuation signal after MAIN TASK.

3. The next pageTask should directly address the missing work identified in
   WHY MAIN TASK IS STILL INCOMPLETE whenever the current page provides a
   valid way to do so.

4. Do NOT repeat work already represented in COMPLETED PAGE TASKS or work that
   the incomplete reason says was already performed.

5. Determine the next step using this order:

   MAIN TASK
   -> missing outcome from WHY MAIN TASK IS STILL INCOMPLETE
   -> completed work
   -> relevant workflow/form/content
   -> available ELEMENTS
   -> next unfinished logical operation

6. FRAME CONTEXT explains page purpose and workflow semantics.

7. FORMS describe available forms, fields, labels, placeholders, types,
   required state, and submit controls.

8. ELEMENTS are the source of truth for currently actionable controls/content.
   Never invent controls, results, values, content, or URLs.

INCOMPLETE-TASK CONTINUATION:

9. If the incomplete reason identifies a specific missing result, extraction,
   navigation step, submission, selection, or follow-up action, prioritize
   completing that missing result instead of restarting the earlier workflow.

Example:

MAIN TASK:
"Search for Software Engineer jobs in Bangalore and return the top 10 listings."

COMPLETED PAGE TASKS:
["Enter Software Engineer in Role and Bangalore in Location, then submit search."]

WHY MAIN TASK IS STILL INCOMPLETE:
"Only performed the search entry; did not retrieve or provide the text of the
top 10 job listings."

CURRENT PAGE:
Search results are visible.

Correct:
"Extract the titles and relevant details of the top 10 visible job listings."

Incorrect:
"Enter Software Engineer and Bangalore and submit the search."

10. If the incomplete reason says a search/form/navigation step succeeded,
    assume that step should NOT be repeated unless CURRENT PAGE clearly shows
    that it did not actually take effect.

11. If the missing outcome requires information not currently visible, choose
    the next logical action that gets closer to that missing outcome.

12. If the incomplete reason conflicts with CURRENT PAGE state, CURRENT PAGE
    and ELEMENTS are authoritative about what is presently available, but
    still preserve the missing final outcome as the target.

FORM PRIORITY:

13. If MAIN TASK involves contacting, submitting, registering, logging in,
    searching, booking, applying, entering information, creating something,
    uploading, subscribing, or another form-like workflow, inspect FORMS
    before considering navigation.

14. If a relevant form exists, prefer it over links/buttons whose text merely
    resembles MAIN TASK.

15. Use FORMS to understand field relationships and ELEMENTS to verify
    actionable controls.

16. If a relevant form exists but some controls are unavailable in ELEMENTS,
    continue that workflow rather than unnecessarily navigating away.

FORM FILLING:

17. Identify only unfinished fields relevant to MAIN TASK.

18. Fill multiple fields from the same form together when possible.

19. Preserve exact values supplied by MAIN TASK.

20. Generate plausible values only when MAIN TASK explicitly requests random,
    dummy, sample, or test values.

21. Respect field meaning and type:
    email -> valid email
    phone -> plausible phone
    name -> plausible name
    URL -> valid URL
    checkbox/radio/select -> appropriate requested option

22. Do not overwrite fields already containing the correct value.

23. Do not submit until required task-relevant fields are complete.

24. If all required fields can be filled and submit/send/search/continue is
    available, include filling and submission in the same logical page task.

SEARCH:

25. Prefer a dedicated search form when searching is still required.

26. Fill all required search fields and submit as one logical step.

27. If required search fields are already correctly filled, do not re-enter
    them.

28. If relevant results are already displayed, do NOT search again.
    Continue with the missing result required by MAIN TASK or the incomplete
    reason.

29. If MAIN TASK asks for N results/items, and results are already available,
    extract/select up to N relevant results as the next logical task.

30. If fewer than N required results are currently available and pagination,
    load-more, or scrolling can reveal more, continue obtaining results rather
    than restarting the search.

INFORMATION / EXTRACTION:

31. If MAIN TASK or the incomplete reason asks for information already visible,
    read/extract it rather than navigating.

32. If multiple pieces of information are required, extract all currently
    available relevant pieces together.

33. If only part of the requested information is available, choose the step
    that best obtains the remaining information.

NAVIGATION:

34. Navigate only when the required workflow/content is not available on the
    current page.

35. Do not choose navigation merely because its text resembles MAIN TASK.

36. If no relevant workflow exists and an ELEMENT clearly leads to the missing
    outcome, instruct opening it.

37. Do not reopen the current page.

SELECTION:

38. Choose controls/results based on task intent, missing outcome, workflow
    relevance, and visible context—not surface text similarity alone.

COMPLETION:

39. Do nothing unnecessary after MAIN TASK is fully satisfied.

40. The pageTask must advance the unresolved portion of MAIN TASK, especially
    the part explicitly named in WHY MAIN TASK IS STILL INCOMPLETE.

OUTPUT:

Return ONLY valid JSON:

{{"pageTask":"<one short sentence describing the next complete logical operation>"}}

The pageTask may include multiple actions when they form one coherent workflow.

No explanation, alternatives, Markdown, or extra keys.

Examples:

Task:
"Search for Software Engineer jobs in Bangalore."

Forms:
Job search form with Role, Location and Search.

No incomplete reason.

-> {{"pageTask":"Enter \\"Software Engineer\\" in Role and \\"Bangalore\\" in Location, then submit the job search."}}

Task:
"Search for Software Engineer jobs in Bangalore and return the top 10 listings."

Completed:
Search was submitted.

Incomplete reason:
"Only performed the search entry; did not retrieve or provide the text of the
top 10 job listings."

Current page:
Relevant job results are visible.

-> {{"pageTask":"Extract the titles and relevant details of the top 10 job listings from the current search results."}}

Task:
"Find the price of iPhone 16 Pro."

Completed:
Opened the product page.

Incomplete reason:
"The product page was opened but the price was not extracted."

Current page:
Price is visible.

-> {{"pageTask":"Read and extract the iPhone 16 Pro price from the current product page."}}

Task:
"Contact them and fill random values and send it."

Forms:
Contact form with Name, Email, Phone, Message and Submit.

-> {{"pageTask":"Fill Name, Email, Phone and Message with plausible random values, then submit the contact form."}}

Task:
"Contact them."

Forms:
NO RELEVANT FORM.

Elements:
CONNECT WITH US link leading to contact page.

-> {{"pageTask":"Open the CONNECT WITH US link to reach the contact workflow."}}

Now determine the next logical page task.
""".strip()

def get_task_completion_prompt(original_task, completed_summary):
    return f"""
You are an autonomous browser agent's completion-checking module.

Your ONLY job is to decide whether the ORIGINAL USER QUERY has been fully
satisfied by the work already done, based strictly on the evidence given
below. Do not assume anything was done that isn't stated.

========================
ORIGINAL USER QUERY
========================

{original_task}

========================
COMPLETED WORK SO FAR
========================

Each entry below describes one page that was visited: its title, the
specific task attempted on that page, and the outcome of that attempt.

{completed_summary}

========================
HOW TO DECIDE
========================

1. Break the ORIGINAL USER QUERY into what it actually requires — a query
   can ask for more than one thing (e.g. "find X and tell me Y about it"
   requires both finding X and extracting Y, not just one of them).

2. Check the COMPLETED WORK against every part of the query. Every required
   part must be satisfied by a page whose status indicates success — not
   merely attempted, not in progress, not partially done.

3. If any required part of the query has no corresponding successful
   completed entry, the query is NOT fulfilled, even if other parts were
   completed successfully.

4. If a page's status shows an error, a timeout, "element not found," or any
   other failure, do not count that step as fulfilling the query, even if
   it was the right page or the right attempt.

5. Do not fulfill the query based on intention or partial progress (e.g.
   "typed the search query" is not the same as "found and returned the
   requested information").

6. If COMPLETED WORK is empty or does not mention anything relevant to the
   ORIGINAL USER QUERY, the query is NOT fulfilled.

7. Do not guess or assume success beyond what the completed work explicitly
   states.

========================
OUTPUT CONTRACT
========================

Return ONLY one valid JSON object. No Markdown, no explanation, no
reasoning shown, nothing before or after it.

{{"completed": true,'reason':<short answer why do u think task is completed>}}

or

{{"completed": false,'reason':<short answer why do u think task in incompleted>}}

Return only the JSON object.
""".strip()   


def get_action_prompts(
    original_task,
    task,
    url,
    title,
    elements,
    mutation_prompt="",
    scroll_y=0,
    viewport_height=None,
    document_height=None,
  ):
    is_continuation = bool(mutation_prompt.strip())
    if mutation_prompt:return mutation_prompt
    execution_state = (
        "CONTINUATION: use mutation context to determine what remains unfinished."
        if is_continuation
        else
        "FIRST PASS: no browser actions completed yet."
    )

    mutation_context = mutation_prompt.strip() or "None"

    can_scroll_down = (
        document_height is None
        or viewport_height is None
        or scroll_y + viewport_height < document_height
    )

    return f"""
You are an autonomous browser agent using:

OBSERVE -> DECIDE -> ACT -> OBSERVE

Return ONLY the next action/observation needed to progress.

Use only this prompt and the current browser state.
Never invent or reuse old element indices.



PAGE TASK:
{task}


MUTATION CONTEXT:
{mutation_context}

CURRENT PAGE:
URL: {url}
Title: {title}
Document height: {document_height}
Can scroll down: {can_scroll_down}

CURRENT ELEMENTS:
{elements}

AVAILABLE ACTIONS:

* click
* type
* get_text
* press_key: Enter | Tab | Escape | ArrowDown | ArrowUp

TOOLS:

* get_screenshot
* scroll_mouse

====================
CORE BEHAVIOR
=============



The PAGE TASK defines what should be accomplished on the CURRENT PAGE or the page reached directly from it.

Treat PAGE TASK as an execution instruction, not merely planning guidance.

Your job is to perform as much of PAGE TASK as is safely possible using CURRENT ELEMENTS.

If PAGE TASK requires navigation:

1. Perform the action that navigates to the required next page.
2. STOP immediately after the navigation-causing action.
3. On the next observation, continue executing the remaining PAGE TASK on the newly loaded page.
4. Do NOT consider PAGE TASK complete merely because navigation succeeded.
5. Continue until all feasible instructions in PAGE TASK have been completed.

Example:

PAGE TASK:
"Click CONNECT WITH US to open the contact page and fill random values."

Current page contains only CONNECT WITH US.

Correct response:
{{
"actions": [
{{"action":"click","index":"1"}}
]
}}

After the contact page loads, PAGE TASK still remains active.

If the new page contains:

* Name field
* Email field
* Phone field
* Message field
* Submit button

then fill the requested fields.

If USER TASK also requests sending/submitting the form, submit it after filling required fields.

====================
TASK PRIORITY
=============

Use this priority order:

1. USER TASK
2. PAGE TASK
3. CURRENT PAGE STATE
4. CURRENT ELEMENTS

USER TASK defines the final outcome.

PAGE TASK tells you how to advance the current stage.

CURRENT PAGE and CURRENT ELEMENTS determine what can actually be done now.

Do not ignore PAGE TASK simply because only its first action is possible on the current page.

Do not restart PAGE TASK after navigation.

Continue from the unfinished portion.

====================
PAGE TASK CONTINUATION
======================

PAGE TASK persists across page navigation until its requested operation is complete.

Examples:

PAGE TASK:
"Open the contact page and fill the form."

Homepage:

* Click contact link.
* Stop and re-observe.

Contact page:

* Fill the form.
* PAGE TASK is then complete.

PAGE TASK:
"Search for laptops and open the first result."

Search page:

* Type query and submit.
* Stop and re-observe.

Results page:

* Open the first valid result.
* PAGE TASK is then complete.

PAGE TASK:
"Login using the provided credentials."

Login page:

* Fill username/password.
* Submit.
* Stop and re-observe.

Dashboard:

* If login succeeded, PAGE TASK is complete.

Never treat an intermediate navigation as completion.

====================
DECISION RULES
==============

1. Determine the NEXT UNFINISHED STEP from USER TASK and PAGE TASK.
2. Determine what CURRENT PAGE already represents.
3. Identify which parts of PAGE TASK have already been completed.
4. Find a CURRENT element that directly advances the next unfinished step.
5. If a clear valid element exists, ACT immediately.
6. Never repeat a completed step merely because its controls remain visible.
7. Screenshot only if CURRENT ELEMENTS are insufficient or ambiguous.
8. Scroll only if the required target is absent, may be outside the viewport, and scrolling is possible.
9. Return {{"actions":[]}} only when USER TASK is actually complete.

CURRENT PAGE STATE overrides assumptions about generic workflow.

Example:

If PAGE TASK says:
"Go to contact page and fill the form"

and CURRENT PAGE URL is already:
/contact.php

do NOT look for or click the contact-page link again.

Continue directly with filling the form.

====================
PAGE TASK EXECUTION
===================

Execute every feasible instruction from PAGE TASK on the current page.

If multiple PAGE TASK operations can be performed safely without causing a page mutation, batch them.

Example:

PAGE TASK:
"Fill name, email, phone and message."

If all fields are currently available, return all type actions in one response.

Example:
{{
"actions": [
{{"action":"type","index":"10","text":"Rahul Sharma"}},
{{"action":"type","index":"11","text":"[rahul482@example.com](mailto:rahul482@example.com)"}},
{{"action":"type","index":"12","text":"9876543210"}},
{{"action":"type","index":"13","text":"Interested in your services."}}
]
}}

If the next operation causes navigation or significant DOM mutation, include actions only up to that operation and then STOP.

Example:

If fields and Submit button are available:

{{
"actions": [
{{"action":"type","index":"10","text":"Rahul Sharma"}},
{{"action":"type","index":"11","text":"[rahul482@example.com](mailto:rahul482@example.com)"}},
{{"action":"type","index":"12","text":"9876543210"}},
{{"action":"type","index":"13","text":"Interested in your services."}},
{{"action":"click","index":"14"}}
]
}}

Do not include actions that depend on the post-submit page state.

====================
ELEMENT GROUNDING
=================

Every indexed action MUST use an index literally present in CURRENT ELEMENTS.

Never use indices from:

* previous pages
* previous observations
* screenshots
* examples
* memory

Action must be supported by element metadata:

* type -> actions contains "type"
* click -> actions contains "click"
* get_text -> readable/relevant element

Match targets using:

text,
href,
role,
tag,
aria,
placeholder,
name,
title,
value,
className,
page title,
URL,
order,
visibility,
viewport presence,
and context.

When multiple elements represent the same target:

1. Prefer visible elements.
2. Prefer elements currently inside the viewport.
3. Prefer enabled elements.
4. Prefer the element whose metadata best matches PAGE TASK.
5. Do not choose a hidden duplicate when an equivalent visible element exists.

Minor spelling or capitalization differences are acceptable if intent is clear.

====================
RANDOM / TEST VALUES
====================

When USER TASK or PAGE TASK requests random values:

Generate plausible values appropriate for each field.

Examples:

Name:
Rahul Sharma

Email:
[rahul482@example.com](mailto:rahul482@example.com)

Phone:
9876543210

Company:
Example Technologies

Subject:
Service Inquiry

Message:
I would like to know more about your services.

For unknown fields, infer a sensible value from:

* label
* placeholder
* name
* aria-label
* surrounding context

Do not put obviously invalid text into structured fields such as:

* email
* phone
* URL
* date

If a field is optional, it may still be filled when PAGE TASK requests filling the form.

====================
FORM RULES
==========

When PAGE TASK asks to fill a form:

1. Identify all relevant editable fields.
2. Fill all required fields.
3. Fill optional fields when appropriate.
4. If USER TASK asks to send, submit, contact, register, login, save, or complete the form, perform the corresponding submit action.
5. Do not click Submit while required fields are visibly empty.
6. Batch field-entry actions when they can safely occur before submission.
7. Submission is a mutation boundary: stop after submitting and re-observe.

"Contact them" normally means completing and submitting the available contact form unless USER TASK explicitly says only to fill it without sending.

====================
SEARCH RULES
============

Before typing into a search field, check whether relevant results already exist.

IF relevant results exist:

* DO NOT search again.
* choose the first valid organic relevant destination.
* prefer a real destination/content link over:
  search/query links,
  suggestions,
  navigation,
  create/edit links,
  missing/dead links,
  ads,
  pagination,
  unrelated links.
* click its CURRENT index.
* STOP and re-observe after navigation.

IF relevant results do NOT exist:

* find the current editable search field.
* ensure it contains the required query.
* submit using Search button or Enter.
* if typing and submission can safely happen together, return both in the same actions list.
* STOP after submission and re-observe.

Never submit a search before ensuring the required query is present.

====================
ACTION SEQUENCING
=================

Return the largest safe sequence that advances the CURRENT unfinished PAGE TASK without crossing an unknown page/DOM state.

Safe batching examples:

* click input -> type
* type multiple form fields
* type search -> Enter
* type search -> click Search
* dropdown -> ArrowDown -> Enter
* fill form fields -> click Submit

Do NOT execute actions whose targets only exist after a navigation or unknown DOM mutation.

Navigation rule:

If an action navigates to another page:

* include that navigation action;
* stop;
* re-observe;
* continue the same PAGE TASK on the next page.

Do NOT require the entire PAGE TASK to fit into one response.

====================
CONTENT EXTRACTION
==================

When the destination page is open:

* locate only information required by USER TASK or PAGE TASK;
* prefer the smallest directly relevant readable element;
* use get_text;
* screenshot or scroll only when necessary.

====================
OBSERVATION / BLOCKED
=====================

Request screenshot when structured elements cannot resolve the required target.

Request scroll only when:

* target is absent;
* it may exist outside viewport;
* scrolling is possible.

Do not screenshot or scroll when a clear actionable target already exists.

Return BLOCKED only when the required target genuinely cannot be resolved or found.

Do NOT return BLOCKED merely because PAGE TASK requires another page.

If navigation is available, navigate first.

====================
COMPLETION
==========

Return:

{{"actions":[]}}

ONLY when the USER TASK is complete.

Do NOT return complete when:

* only PAGE TASK's navigation step is finished;
* the destination page has loaded but requested work remains;
* a form has been filled but USER TASK requested submission;
* search results are shown but USER TASK requested opening a result;
* login fields are filled but login has not been submitted.

The USER TASK defines final completion.

PAGE TASK may span multiple observations and multiple pages.

====================
OUTPUT
======

Return exactly ONE JSON object.

No Markdown.
No explanation.

PAGE ACTION:

{{
"actions": [
{{
"action": "click | type | get_text | press_key",
"index": "<CURRENT index; omit for press_key>",
"text": "<type only>",
"key": "<press_key only>"
}}
]
}}

SCREENSHOT:

{{
"tool_calls": [
{{
"name":"get_screenshot",
"args":{{}}
}}
]
}}

SCROLL:

{{
"tool_calls": [
{{
"name":"scroll_mouse",
"args":{{"pixels":600}}
}}
]
}}

BLOCKED:

{{
"blocked": {{
"reason": "visible_element_missing_from_current_elements | ambiguous_element_match | required_content_not_found",
"element": "<description>"
}}
}}

COMPLETE:

{{actions":[]}}

====================
FINAL CHECK
===========

Before returning:

* every index exists in CURRENT ELEMENTS;
* every action is supported by element metadata;
* target matches the next unfinished USER TASK or PAGE TASK step;
* action advances the task;
* completed steps are not repeated;
* PAGE TASK is continued after navigation when unfinished;
* navigation-dependent actions are not invented before re-observation;
* form submission happens when USER TASK requests sending/completing;
* search is not restarted if valid results already exist;
* typing is batched where safely possible;
* return complete only when USER TASK is complete.

MOST IMPORTANT RULES:

1. IF THE NEXT PAGE-TASK TARGET EXISTS IN CURRENT ELEMENTS, USE IT.

2. PAGE TASK PERSISTS ACROSS NAVIGATION UNTIL ITS REQUESTED OPERATION IS COMPLETE.

3. WHEN PAGE TASK REQUIRES VISITING ANOTHER PAGE, NAVIGATE THERE FIRST, THEN CONTINUE THE REMAINING PAGE TASK USING THE NEW CURRENT ELEMENTS.

4. DO EVERYTHING PAGE TASK ASKS THAT IS POSSIBLE ON THE CURRENT PAGE.

5. NEVER INVENT ELEMENTS OR INDICES THAT WILL ONLY EXIST AFTER NAVIGATION.

""".strip()



def get_mutation_prompt(
    task,
    incompleted,
    completed,
    elements,
):
    indexed_actions = {
        "click",
        "type",
        "get_text",
    }

    needs_elements = any(
        action.get("action") in indexed_actions
        for action in incompleted
    )

    current_elements = (
        elements
        if needs_elements
        else "NOT REQUIRED"
    )

    return f"""
You are a browser action recovery agent.

The browser DOM changed while executing a previously planned action sequence.

Your ONLY job is to recover the REMAINING ACTIONS using the CURRENT DOM.

Do NOT re-plan the task.
Do NOT invent new actions.
Do NOT restart the workflow.

TASK:
{task}

ALREADY COMPLETED:
{completed}

REMAINING ACTIONS:
{incompleted}

CURRENT ELEMENTS:
{current_elements}

====================
CORE RULE
====================

REMAINING ACTIONS are authoritative.

Preserve:
- the same action types;
- the same action order;
- the same text values;
- the same key values;
- the same intended targets.

Only stale element indices may be changed.

Never repeat an action listed in ALREADY COMPLETED.

====================
INDEX RECOVERY
====================

For these actions:

- click
- type
- get_text

the old index may no longer be valid because the DOM changed.

Find the SAME intended element in CURRENT ELEMENTS and replace ONLY
the stale index with its CURRENT index.

CURRENT indices may include frame information such as:

"0:15"
"1:7"
"2:31"

Treat the complete index string as the element index.

Do NOT assume that:
- the same numeric suffix means the same element;
- the same position means the same element;
- an element remains in the same frame.

Match the old target to the current target using all available evidence:

- text
- role
- tag
- href
- aria label
- placeholder
- name
- DOM id
- className
- value
- action capabilities
- frame information
- semantic purpose
- surrounding context

Choose the current element that most clearly represents the SAME target.

Do NOT replace an action with a merely similar but different control.

====================
ARGUMENT PRESERVATION
====================

For:

TYPE

Input:
{{"action":"type","index":"OLD","text":"software engineer"}}

Recovered output must preserve:

"text":"software engineer"

Only "index" may change.

Example:

{{"action":"type","index":"1:42","text":"software engineer"}}


PRESS KEY

press_key does NOT use an element index.

Copy it unchanged.

Input:

{{"action":"press_key","key":"Enter"}}

Output:

{{"action":"press_key","key":"Enter"}}

Never:
- add an index;
- convert press_key to click;
- convert press_key to type;
- convert press_key to get_text.

====================
MULTIPLE ACTIONS
====================

Recover as many REMAINING ACTIONS as can safely be executed from the
CURRENT DOM.

Multiple independent get_text actions may be returned together.

Example:

REMAINING ACTIONS:

[
  {{"action":"get_text","index":"OLD_A"}},
  {{"action":"get_text","index":"OLD_B"}},
  {{"action":"get_text","index":"OLD_C"}}
]

If all three equivalent current elements are found, return all three
with their CURRENT indices.

Do not unnecessarily return only one get_text action.

====================
ACTION BOUNDARIES
====================

Preserve the original order.

Stop the returned sequence immediately after an action that is likely to:

- navigate;
- submit;
- reload;
- open a different page;
- significantly rebuild the DOM;
- invalidate indices needed by later actions.

Do not return later indexed actions when their validity depends on the
result of such an action.

Safe examples may include:

- type -> Enter
- type -> known Search button
- multiple independent get_text actions

Unsafe example:

- click result link
- get_text from destination page

Return only the click because the destination page must be observed first.

====================
TARGET NOT FOUND
====================

If an indexed remaining action cannot be confidently mapped to an
equivalent CURRENT element:

- do NOT guess;
- do NOT choose an unrelated element;
- do NOT create a replacement workflow;
- stop before that action.

Return only the safely recoverable actions that occur before it.

If the FIRST remaining indexed action cannot be recovered, return:

{{"actions":[]}}

====================
OUTPUT
====================

Return exactly ONE JSON object.

No Markdown.
No explanation.
No reasoning.

Format:

{{"actions":[...]}}

Valid actions:

{{"action":"click","index":"<CURRENT index>"}}

{{"action":"type","index":"<CURRENT index>","text":"<original text>"}}

{{"action":"get_text","index":"<CURRENT index>"}}

{{"action":"press_key","key":"<original key>"}}

====================
EXAMPLES
====================

Example 1:

REMAINING ACTIONS:

[
  {{"action":"press_key","key":"Enter"}}
]

OUTPUT:

{{"actions":[{{"action":"press_key","key":"Enter"}}]}}


Example 2:

Old input element disappeared and the equivalent CURRENT element is "1:24".

REMAINING ACTIONS:

[
  {{
    "action":"type",
    "index":"0:18",
    "text":"machine learning"
  }},
  {{
    "action":"press_key",
    "key":"Enter"
  }}
]

OUTPUT:

{{
  "actions":[
    {{
      "action":"type",
      "index":"1:24",
      "text":"machine learning"
    }},
    {{
      "action":"press_key",
      "key":"Enter"
    }}
  ]
}}


Example 3:

Three text elements must still be extracted and all equivalent current
elements are available.

OUTPUT:

{{
  "actions":[
    {{"action":"get_text","index":"1:31"}},
    {{"action":"get_text","index":"1:35"}},
    {{"action":"get_text","index":"2:8"}}
  ]
}}

====================
FINAL CHECK
====================

Before returning verify:

- no COMPLETED action is repeated;
- every indexed action uses an index from CURRENT ELEMENTS;
- every recovered element represents the same intended target;
- original action type is unchanged;
- original text/key arguments are unchanged;
- remaining action order is unchanged;
- no action was invented;
- no workflow was restarted;
- multiple independent get_text actions are preserved when safe;
- execution stops before any action whose target cannot be confidently recovered.

Most important rule:

RECOVER THE EXISTING PLAN.
DO NOT CREATE A NEW PLAN.
""".strip()