from playwright.async_api import Locator
from collections import defaultdict
from State import WebState
import numpy as np
from collections import defaultdict

# async def get_page_details(page):
#     elements = await page.evaluate("""
#     () => {
#         const nodes = document.querySelectorAll(
#             'button,a,input,select,textarea,p,h1,h2,h3,h4,h5,h6,form,textbox,seaerchbox'
#         );

#         return Array.from(nodes)
#             .filter(el => {
#                 if (el.offsetParent === null) return false;

#                 const text = (el.innerText || "").trim();
#                 const placeholder = (el.placeholder || "").trim();

#                 return text || placeholder;
#             })
#             .map((el, i) => {
#                 el.setAttribute("data-agent-id", i);

#                 return {
#                     index: i,
#                     role: el.tagName.toLowerCase(),

#                     text: (el.innerText || "").trim(),
#                     placeholder: (el.placeholder || "").trim(),

#                     id: el.id || "",
#                     name: el.name || "",
#                     type: el.type || "",
#                     value: el.value || "",
#                     class: el.className || "",

#                     ariaLabel: el.getAttribute("aria-label") || "",
#                     title: el.title || "",

#                     href: el.href || "",

#                     verification: {
#                         tag: el.tagName.toLowerCase(),
#                         id: el.id || "",
#                         class: el.className || "",
#                         name: el.name || "",
#                         type: el.type || "",
#                         placeholder: el.placeholder || "",
#                         text: (el.innerText || "").trim()
#                     }
#                 };
#             });
#     }
#     """)

#     d = defaultdict(dict)
#     for e in elements:
#         e["summary"] = (
#                 "< "
#                 + ", ".join(
#                     part for part in [
#                         f'role={e["role"]}' if e.get("role") else "",
#                         f'index={e["index"]}' if e.get("index") is not None else "",
#                         f'type={e["type"]}' if e.get("type") else "",
#                         f'placeholder={e["placeholder"][:30]}' if e.get("placeholder") else "",
#                         f'ariaLabel={e["ariaLabel"][:30]}' if e.get("ariaLabel") else "",
#                         f'text={e["text"][:40]}' if e.get("text") else "",
#                         f'value={e["value"][:40]}' if e.get("value") else "",
#                         f'title={e["title"][:40]}' if e.get("title") else "",
#                         f'id={e["id"][:40]}' if e.get("id") else "",
#                         f'class={e["class"][:40]}' if e.get("class") else "",
#                     ]
#                     if part
#                 )
#                 + " >"
#             )
#         d[e["role"]][e["index"]] = e


#     return d


async def get_page_details(page):
    elements = await page.evaluate("""
() => {

    const isVisible = (el) => {
        const style = window.getComputedStyle(el);
        const rect = el.getBoundingClientRect();

        return (
            style.visibility !== "hidden" &&
            style.display !== "none" &&
            rect.width > 0 &&
            rect.height > 0
        );
    };

    const interactive = `
        button,
        a,
        input,
        textarea,
        select,
        option,
        summary,
        details,
        [role],
        [tabindex],
        [contenteditable="true"]
    `;

    const nodes = [...document.querySelectorAll(interactive)];

    return nodes
        .filter(el => isVisible(el))
        .map((el, i) => {

            if (!el.hasAttribute("data-agent-id")) {
                el.setAttribute("data-agent-id",i);
            }

            const rect = el.getBoundingClientRect();

            const role =
                el.getAttribute("role") ||
                el.tagName.toLowerCase();

            let actions = [];

            switch (el.tagName.toLowerCase()) {
                case "input":
                    actions = ["click","type"];
                    break;

                case "textarea":
                    actions = ["click","type"];
                    break;

                case "select":
                    actions = ["click","select"];
                    break;

                case "button":
                    actions = ["click"];
                    break;

                case "a":
                    actions = ["click"];
                    break;

                default:
                    actions = ["click"];
            }

            return {

                id: el.getAttribute("data-agent-id"),

                role,
                tag: el.tagName.toLowerCase(),

                text: (el.innerText || "").trim(),

                placeholder: el.placeholder || "",

                value: el.value || "",

                type: el.type || "",

                name: el.name || "",

                domId: el.id || "",

                className: el.className || "",

                ariaLabel:
                    el.getAttribute("aria-label") || "",

                title: el.title || "",

                href: el.href || "",

                enabled: !el.disabled,

                checked: !!el.checked,

                selected: !!el.selected,

                readonly: !!el.readOnly,

                required: !!el.required,

                focused:
                    document.activeElement === el,

                actions,

                bbox: {
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height),

                    centerX: Math.round(rect.left + rect.width/2),
                    centerY: Math.round(rect.top + rect.height/2)
                }
            };
        });
}
""")

    grouped = defaultdict(dict)

    for e in elements:

        summary_parts = [

            f'role={e["role"]}',

            f'id={e["id"][:8]}',

            f'tag={e["tag"]}' if e["tag"] else "",
            f'type={e["type"]}' if e["type"] else "",

            f'text="{e["text"][:40]}"' if e["text"] else "",
            f'name="{e["name"][:40]}"' if e["name"] else "",
            f'domId="{e["domId"]}"' if e["domId"] else "",
            f'className="{e["className"]}"' if e["className"] else "",
            f'href="{e["href"]}"' if e["href"] else "",
            f'enabled="{e["enabled"]}"' if e["enabled"] else "",
            f'checked="{e["checked"]}"' if e["checked"] else "",
            f'selected="{e["selected"]}"' if e["selected"] else "",
            f'required="{e["required"]}"' if e["required"] else "",

            f'placeholder="{e["placeholder"][:40]}"'
                if e["placeholder"] else "",

            f'aria="{e["ariaLabel"][:40]}"'
                if e["ariaLabel"] else "",

            f'value="{e["value"][:30]}"'
                if e["value"] else "",

            f'actions={",".join(e["actions"])}',

            f'pos=({e["bbox"]["centerX"]},{e["bbox"]["centerY"]})'
        ]

        e["summary"] = "< " + ", ".join(
            p for p in summary_parts if p
        ) + " >"

        grouped[e["role"]][e["id"]] = e

    return grouped
async def get_locators(page, element, ids):
    role = ""
    for k, v in element.items():
        if ids in v.keys():
            role = k
            break

    v = element[role][ids]
    locators = []

    # PRIMARY: data-agent-id — unique by construction, always try this first
    locators.append(page.locator(f'[data-agent-id="{ids}"]'))

    # fallback chain — only matters if data-agent-id is gone (element was recreated)
    idv = v.get("id", "")
    name = v.get("name", "")
    placeholder = v.get("placeholder", "")
    arialabel = v.get("ariaLabel", "")
    text = v.get("text", "")
    cls = v.get("class", "")
    tag = v.get("role", "")

    if idv:
        locators.append(page.locator(f'#{idv}'))
    if name:
        locators.append(page.locator(f'[name="{name}"]'))
    if placeholder:
        locators.append(page.get_by_placeholder(placeholder))
    if arialabel:
        locators.append(page.get_by_label(arialabel))
    if text:
        locators.append(page.get_by_text(text, exact=True))
    if cls and tag:
        cls_selector = ".".join(c for c in cls.split() if c)
        locators.append(page.locator(f'{tag}.{cls_selector}'))
    if tag:
        locators.append(page.locator(tag))

    return locators

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

# def get_k_relevant_elements(task, elements, embedder, top_k=15):
#     def flatten_elements(elements_dict):
#         flatter = {}
#         for role, items in elements_dict.items():
#             flat = {}
#             for idx, el in items.items():
#                 text = el.get("text", "").strip()
#                 aria_label = el.get("ariaLabel", "").strip()
#                 if text or aria_label:  # skip elements with nothing to embed
#                     flat[el["index"]] =el['summary'][1:-1]
#             if flat:
#                 flatter[role] = flat
#         return flatter

#     flattened = flatten_elements(elements)
#     task_embedding = embedder.encode([task])[0]

#     def cosine_sim(a, b):
#         return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

#     result = {}
#     for role, items in flattened.items():
#         entries = list(items.values())
#         #texts = [e["text"] + " " + e["aria_label"] for e in entries]
#         texts =[]
#         for e in entries:
#             texts.append(e)
#         embeddings = embedder.encode(texts)  # embed once per role, in one batch

#         scored = [
#             (cosine_sim(task_embedding, emb), el)
#             for emb, el in zip(embeddings, entries)
#         ]
#         scored.sort(key=lambda x: x[0], reverse=True)

#         result[role] = [el for score, el in scored[:top_k]]

#     return result
import numpy as np
from collections import defaultdict


def cosine_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def get_k_relevant_elements(task, elements, embedder, top_k=15):
    """
    Returns the globally most relevant elements.

    elements:
    {
        "button": {
            0: {...},
            1: {...}
        },
        "input": {
            2: {...}
        }
    }
    """

    flat_elements = []

    # Flatten all roles
    for role, items in elements.items():
        for idx, el in items.items():
            summary = el.get("summary", "").strip()

            if not summary:
                continue

            flat_elements.append({
                "role": role,
                "index": idx,
                "summary": summary,
                "element": el,
            })

    if not flat_elements:
        return {}

    # Encode everything in one batch
    texts = [x["summary"] for x in flat_elements]

    task_embedding = embedder.encode([task])[0]
    element_embeddings = embedder.encode(texts)

    scored = []

    for info, emb in zip(flat_elements, element_embeddings):
        score = cosine_sim(task_embedding, emb)
        scored.append((score, info))

    scored.sort(key=lambda x: x[0], reverse=True)

    # Keep global top-k
    scored = scored[:top_k]

    # Group back by role
    result = defaultdict(dict)

    for score, info in scored:
        el = info["element"].copy()
        summ=el['summary']
        result[info["role"]][info["index"]] = summ

    return dict(result)