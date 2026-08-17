
from playwright.async_api import Locator
from collections import defaultdict
import numpy as np
from collections import defaultdict
async def get_page_details(page):

    all_elements = defaultdict(dict)
    all_forms = []

    frames = page.frames

    global_id = 0

    for frame_index, frame in enumerate(frames):

        try:
            result = await frame.evaluate("""
() => {

    const isVisible = (el) => {
        if (!el || !(el instanceof Element)) {
            return false;
        }

        const rect = el.getBoundingClientRect();

        if (rect.width <= 0 || rect.height <= 0) {
            return false;
        }

        let current = el;

        while (
            current &&
            current !== document.documentElement
        ) {
            const style = window.getComputedStyle(current);

            if (
                style.display === "none" ||
                style.visibility === "hidden" ||
                style.visibility === "collapse" ||
                parseFloat(style.opacity || "1") <= 0
            ) {
                return false;
            }

            current = current.parentElement;
        }

        return (
            rect.bottom > 0 &&
            rect.right > 0 &&
            rect.top < window.innerHeight &&
            rect.left < window.innerWidth
        );
    };


    // ==========================================
    // ELEMENTS
    // ==========================================

    const selector = `
        button,
        a,
        input,
        textarea,
        select,
        option,
        summary,
        details,
        p,
        h1,h2,h3,h4,h5,h6,
        [role],
        [tabindex],
        [contenteditable="true"]
    `;


    const nodes = [
        ...document.querySelectorAll(selector)
    ].filter(isVisible);


    const elements = nodes.map((el, localIndex) => {

        const tag = el.tagName.toLowerCase();

        const role =
            el.getAttribute("role") || tag;

        let actions = [];

        if (
            tag === "input" ||
            tag === "textarea" ||
            role === "textbox"
        ) {
            actions = ["click", "type"];
        }

        else if (
            tag === "select" ||
            role === "combobox"
        ) {
            actions = ["click", "select"];
        }

        else if (
            tag === "button" ||
            tag === "a" ||
            role === "button" ||
            role === "checkbox" ||
            role === "radio"
        ) {
            actions = ["click"];
        }

        else if (
            ["p", "h1", "h2", "h3", "h4", "h5", "h6"]
                .includes(tag)
        ) {
            actions = ["read text"];
        }

        else {
            actions = ["click"];
        }


        return {
            localIndex,

            role,
            tag,

            text:
                (el.innerText || "").trim(),

            placeholder:
                el.getAttribute("placeholder") || "",

            value:
                "value" in el
                    ? String(el.value || "")
                    : "",

            type:
                el.getAttribute("type") || "",

            name:
                el.getAttribute("name") || "",

            domId:
                el.id || "",

            className:
                typeof el.className === "string"
                    ? el.className
                    : "",

            ariaLabel:
                el.getAttribute("aria-label") || "",

            title:
                el.getAttribute("title") || "",

            href:
                el.href || "",

            enabled:
                !el.disabled,

            checked:
                !!el.checked,

            selected:
                !!el.selected,

            readonly:
                !!el.readOnly,

            required:
                !!el.required,

            actions
        };
    });


    // ==========================================
    // FORM DETECTION
    // ==========================================

    const CONTROL_SELECTOR = `
        input:not([type="hidden"]),
        textarea,
        select,
        button,
        [contenteditable="true"],
        [role="textbox"],
        [role="combobox"],
        [role="checkbox"],
        [role="radio"],
        [role="switch"],
        [role="button"]
    `;


    const describeControl = (el) => {

        const parts = [];

        const tag =
            el.tagName.toLowerCase();

        const type =
            el.getAttribute("type");

        const name =
            el.getAttribute("name");

        const placeholder =
            el.getAttribute("placeholder");

        const aria =
            el.getAttribute("aria-label");

        const text =
            (el.innerText || "").trim();

        parts.push(`tag=${tag}`);

        if (type)
            parts.push(`type=${type}`);

        if (name)
            parts.push(`name="${name}"`);

        if (placeholder)
            parts.push(
                `placeholder="${placeholder}"`
            );

        if (aria)
            parts.push(
                `aria="${aria}"`
            );

        if (text)
            parts.push(
                `text="${text.slice(0, 80)}"`
            );

        if (el.required)
            parts.push("required=true");

        if (el.checked)
            parts.push("checked=true");

        return `< ${parts.join(", ")} >`;
    };


    const forms = [];


    // ------------------------------------------
    // Native forms
    // ------------------------------------------

    const nativeForms = [
        ...document.querySelectorAll("form")
    ];

    nativeForms.forEach((form, index) => {

        const controls = [
            ...form.querySelectorAll(
                CONTROL_SELECTOR
            )
        ].filter(isVisible);

        if (!controls.length) {
            return;
        }

        forms.push({
            type: "native",
            controls:
                controls.map(describeControl)
        });
    });


    // ------------------------------------------
    // Semantic / modern JS forms
    // ------------------------------------------

    const candidates = [
        ...document.querySelectorAll(`
            [role="form"],
            fieldset,
            section,
            [role="dialog"],
            main,
            div
        `)
    ];


    const seenControls = new Set();


    for (const container of candidates) {

        const controls = [
            ...container.querySelectorAll(
                CONTROL_SELECTOR
            )
        ].filter(isVisible);


        const editable = controls.filter(el => {

            const tag =
                el.tagName.toLowerCase();

            const role =
                el.getAttribute("role");

            return (
                tag === "input" ||
                tag === "textarea" ||
                tag === "select" ||
                role === "textbox" ||
                role === "combobox" ||
                role === "checkbox" ||
                role === "radio"
            );
        });


        if (editable.length < 1) {
            continue;
        }


        /*
         * Create a signature to prevent the same form
         * being reported through several nested divs.
         */
        const signature = editable
            .map(el =>
                `${el.tagName}:${el.name}:${el.id}:${el.getAttribute("aria-label")}`
            )
            .join("|");


        if (seenControls.has(signature)) {
            continue;
        }

        seenControls.add(signature);


        forms.push({
            type: "semantic",
            controls:
                controls.map(describeControl)
        });
    }


    return {
        elements,
        forms
    };
}
""")


        except Exception as e:
            print(
                f"Skipping frame {frame_index}: {e}"
            )
            continue


        # ==========================================
        # FRAME INFORMATION
        # ==========================================

        frame_url = frame.url

        try:
            frame_name = frame.name
        except Exception:
            frame_name = ""


        # ==========================================
        # ELEMENTS
        # ==========================================

        for e in result.get("elements", []):

            element_id = str(global_id)
            global_id += 1

            e["id"] = element_id
            e["frameIndex"] = frame_index
            e["frameUrl"] = frame_url

            text_limit = (
                400
                if e["tag"] in {
                    "p",
                    "h1",
                    "h2",
                    "h3",
                    "h4",
                    "h5",
                    "h6"
                }
                else 80
            )


            summary_parts = [

                f'role={e["role"]}',

                f'id={element_id}',

                f'frame={frame_index}',

                f'tag={e["tag"]}',

                f'type={e["type"]}'
                    if e["type"]
                    else "",

                f'text="{e["text"][:text_limit]}"'
                    if e["text"]
                    else "",

                f'name="{e["name"][:60]}"'
                    if e["name"]
                    else "",

                f'placeholder="{e["placeholder"][:100]}"'
                    if e["placeholder"]
                    else "",

                f'aria="{e["ariaLabel"][:150]}"'
                    if e["ariaLabel"]
                    else "",

                f'value="{e["value"][:80]}"'
                    if e["value"]
                    else "",

                f'href="{e["href"]}"'
                    if e["href"]
                    else "",

                f'required={e["required"]}'
                    if e["required"]
                    else "",

                f'actions={",".join(e["actions"])}'
            ]


            e["summary"] = (
                "< "
                + ", ".join(
                    x
                    for x in summary_parts
                    if x
                )
                + " >"
            )


            all_elements[
                e["role"]
            ][element_id] = e


        # ==========================================
        # FORMS
        # ==========================================

        for form_index, form in enumerate(
            result.get("forms", [])
        ):

            controls = ", ".join(
                form["controls"]
            )

            all_forms.append(
                f'FRAME {frame_index} '
                f'url="{frame_url}" '
                f'FORM {form_index + 1} '
                f'type={form["type"]} '
                f'controls=[{controls}]'
            )


    forms_text = (
        "\\n".join(all_forms)
        if all_forms
        else "NO VISIBLE FORMS"
    )


    return {
        "elements": all_elements,
        "forms": forms_text
    }

async def get_element_data(elements, element_id):
    for role, role_elements in elements.items():
        if element_id in role_elements:
            return role_elements[element_id]

    return None
def escape_css_attr(value):
    """
    Escape a value used inside:
    [attr="value"]
    """
    if value is None:
        return ""

    return (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\A ")
        .replace("\r", "")
    )


def escape_css_id(value):
    """
    Basic CSS ID escaping.

    Prefer attribute selectors or Playwright semantic locators when
    possible. This is mainly a fallback.
    """
    if value is None:
        return ""

    value = str(value)

    special = [
        "\\", "#", ".", ":", "[", "]",
        "(", ")", " ", "/", "@"
    ]

    for char in special:
        value = value.replace(char, "\\" + char)

    return value


def find_element_by_agent_id(elements, element_id):
    """
    Find element metadata from grouped elements.

    Example structure:
    {
        "input": {
            "29": {...}
        },
        "button": {
            "31": {...}
        }
    }
    """

    element_id = str(element_id)

    for role, role_elements in elements.items():
        if element_id in role_elements:
            return role_elements[element_id]

    return None
async def add_unique_locator(locators, locator, description=""):
    """
    Add locator only when it currently resolves to exactly one element.
    """

    try:
        count = await locator.count()

        if count == 1:
            locators.append({
                "locator": locator,
                "description": description
            })
            return True

    except Exception:
        pass

    return False
def get_element_frame(page, element):
    """
    Resolve the Playwright Frame belonging to an extracted element.
    """

    frame_index = element.get("frameIndex", 0)

    try:
        frame_index = int(frame_index)
    except Exception:
        frame_index = 0

    frames = page.frames

    if frame_index < 0 or frame_index >= len(frames):
        return None

    return frames[frame_index]
async def get_locators(page, elements, element_id):

    element = find_element_by_agent_id(
        elements,
        element_id
    )

    if not element:
        print(
            f"[locator] element id={element_id} "
            "not found in current elements"
        )
        return []

    # ============================================================
    # FRAME
    # ============================================================

    frame = get_element_frame(page, element)

    if not frame:
        print(
            f"[locator] frame not found for "
            f"element={element_id}, "
            f"frameIndex={element.get('frameIndex')}"
        )
        return []

    # ============================================================
    # ELEMENT METADATA
    # ============================================================

    tag = element.get("tag", "")
    role = element.get("role", "")

    dom_id = element.get("domId", "")
    name = element.get("name", "")

    aria = element.get("ariaLabel", "")
    placeholder = element.get("placeholder", "")

    text = element.get("text", "")
    href = element.get("href", "")

    input_type = element.get("type", "")

    local_id = element.get("localId")

    # Your current extractor may only have localIndex.
    if local_id is None:
        local_id = element.get("localIndex")

    locators = []

    # ============================================================
    # 1. INJECTED AGENT ID
    # Best locator when available.
    # ============================================================

    if local_id is not None:

        local_id_str = escape_css_attr(
            str(local_id)
        )

        locator = frame.locator(
            f'[data-agent-local-id="{local_id_str}"]'
        )

        found = await add_unique_locator(
            locators,
            locator,
            "data-agent-local-id"
        )

        # If your extraction actually attaches this attribute,
        # this should normally be enough.
        if found:
            return locators

    # ============================================================
    # 2. TAG + DOM ID
    #
    # IMPORTANT:
    # Do NOT use only "#location".
    #
    # Google example:
    #
    # <symbol id="location">
    # <input id="location">
    #
    # input#location is unique.
    # ============================================================

    if dom_id and tag:

        escaped_id = escape_css_id(dom_id)

        await add_unique_locator(
            locators,
            frame.locator(
                f"{tag}#{escaped_id}"
            ),
            "tag+id"
        )

    # ============================================================
    # 3. TAG + NAME
    # ============================================================

    if tag and name:

        escaped_name = escape_css_attr(name)

        await add_unique_locator(
            locators,
            frame.locator(
                f'{tag}[name="{escaped_name}"]'
            ),
            "tag+name"
        )

    # ============================================================
    # 4. ACCESSIBLE LABEL
    # Excellent for inputs.
    #
    # Google Careers:
    # aria-label="Where?"
    # ============================================================

    if aria:

        try:
            await add_unique_locator(
                locators,
                frame.get_by_label(
                    aria,
                    exact=True
                ),
                "aria-label"
            )
        except Exception:
            pass

    # ============================================================
    # 5. PLACEHOLDER
    # ============================================================

    if placeholder:

        try:
            await add_unique_locator(
                locators,
                frame.get_by_placeholder(
                    placeholder,
                    exact=True
                ),
                "placeholder"
            )
        except Exception:
            pass

    # ============================================================
    # 6. ROLE + ACCESSIBLE NAME
    # ============================================================

    role_map = {
        "button": "button",
        "checkbox": "checkbox",
        "radio": "radio",
        "textbox": "textbox",
        "combobox": "combobox",
        "link": "link",
    }

    normalized_role = role_map.get(role)

    if not normalized_role:

        if tag == "button":
            normalized_role = "button"

        elif tag == "a":
            normalized_role = "link"

        elif tag == "textarea":
            normalized_role = "textbox"

        elif (
            tag == "input"
            and input_type
            not in {
                "checkbox",
                "radio",
                "button",
                "submit"
            }
        ):
            normalized_role = "textbox"

        elif (
            tag == "input"
            and input_type == "checkbox"
        ):
            normalized_role = "checkbox"

        elif (
            tag == "input"
            and input_type == "radio"
        ):
            normalized_role = "radio"

    accessible_name = (
        aria
        or text
        or placeholder
    )

    if normalized_role and accessible_name:

        try:
            await add_unique_locator(
                locators,
                frame.get_by_role(
                    normalized_role,
                    name=accessible_name,
                    exact=True
                ),
                "role+name"
            )
        except Exception:
            pass

    # ============================================================
    # 7. HREF
    # ============================================================

    if tag == "a" and href:

        escaped_href = escape_css_attr(href)

        await add_unique_locator(
            locators,
            frame.locator(
                f'a[href="{escaped_href}"]'
            ),
            "href"
        )

    # ============================================================
    # 8. TEXT FOR BUTTON / LINK
    # ============================================================

    if text and tag in {"button", "a"}:

        try:
            await add_unique_locator(
                locators,
                frame.get_by_text(
                    text,
                    exact=True
                ),
                "exact-text"
            )
        except Exception:
            pass

    # ============================================================
    # 9. COMBINED INPUT ATTRIBUTES
    # Strong fallback.
    # ============================================================

    if tag == "input":

        attrs = ["input"]

        if input_type:
            attrs.append(
                f'[type="{escape_css_attr(input_type)}"]'
            )

        if name:
            attrs.append(
                f'[name="{escape_css_attr(name)}"]'
            )

        if aria:
            attrs.append(
                f'[aria-label="{escape_css_attr(aria)}"]'
            )

        if placeholder:
            attrs.append(
                f'[placeholder="{escape_css_attr(placeholder)}"]'
            )

        selector = "".join(attrs)

        await add_unique_locator(
            locators,
            frame.locator(selector),
            "combined-input"
        )

    # ============================================================
    # RETURN LOCATORS ONLY
    # ============================================================

    print(
        f"[locator] element={element_id} "
        f"frame={element.get('frameIndex', 0)} "
        f"candidates="
        f"{[x['description'] for x in locators]}"
    )

    return [
        x["locator"]
        for x in locators
    ]

async def resolve_locator_by_vote(locators):
    groups = []  # list of {"handle": handle, "locators": [locators...]}

    for loc in locators:
        try:
            if await loc.count() != 1:
                continue  # skip ambiguous or missing matches
            handle = await loc.element_handle()
            if handle is None:
                continue
        except Exception:
            continue

        # check if this handle matches an existing group
        matched_group = None
        for group in groups:
            same = await handle.evaluate("(el, other) => el === other", group["handle"])
            if same:
                matched_group = group
                break

        if matched_group:
            matched_group["locators"].append(loc)
        else:
            groups.append({"handle": handle, "locators": [loc]})

    if not groups:
        return None

    # pick the group with the most agreeing locators
    best_group = max(groups, key=lambda g: len(g["locators"]))
    return best_group["locators"][0]   # any locator in the winning group works

async def click_and_check_mutation(page, locator, timeout=1000):

    # start observing BEFORE the click
    await page.evaluate("""
        () => {
            window.__domChanged = false;
            const observer = new MutationObserver(() => { window.__domChanged = true; });
            observer.observe(document.body, { childList: true, subtree: true, attributes: true });
            window.__domObserver = observer;
        }
    """)

    await locator.click()

    try:
        await page.wait_for_function("window.__domChanged === true", timeout=timeout)
        mutated = True
    except Exception:
        mutated = False

    await page.evaluate("if (window.__domObserver) window.__domObserver.disconnect();")

    return mutated
import numpy as np
from collections import defaultdict


def cosine_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


from collections import defaultdict

def get_k_relevant_elements(task, elements, embedder, top_k=15):
    """
    Returns top_k most relevant elements PER ROLE.

    Example:
    {
        "button": { ... top_k buttons ... },
        "input": { ... top_k inputs ... },
        "a": { ... top_k links ... },
    }
    """

    if not elements:
        return {}

    task_embedding = embedder.encode([task])[0]
    result = defaultdict(dict)

    for role, items in elements.items():
        role_elements = []

        for idx, el in items.items():
            summary = el.get("summary", "").strip()

            if not summary:
                continue

            role_elements.append({
                "index": idx,
                "summary": summary,
                "element": el,
            })

        if not role_elements:
            continue

        # Encode all elements of this role together
        texts = [item["summary"] for item in role_elements]
        embeddings = embedder.encode(texts)

        scored = []

        for info, emb in zip(role_elements, embeddings):
            score = cosine_sim(task_embedding, emb)
            scored.append((score, info))

        # Highest relevance first
        scored.sort(key=lambda x: x[0], reverse=True)

        # Keep top_k for THIS role
        for score, info in scored[:top_k]:
            result[role][info["index"]] = info["summary"]

    return dict(result)