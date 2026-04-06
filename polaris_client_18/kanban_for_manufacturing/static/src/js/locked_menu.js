/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { NavBar } from "@web/webclient/navbar/navbar";
import { onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** All text labels added by this module (exact match or startsWith) */
const KFM_MENU_TEXTS = [
    "Kanban",
    "Kanban for Supply Chain",
    "Kanban for Supply Chain Cards",
    "Kanban for Manufacturing",
    "Kanban for Manufacturing Cards",
    "Place Order",
    "Scan Kanban",
];

const KFM_ELEMENT_SELECTORS = [
    // ── Navbar / top-level menu entries ────────────────────────────────────
    { sel: ".o_menu_sections > *",                         type: "menu"   },
    { sel: ".o_dropdown_menu .o_dropdown_item",            type: "menu"   },
    { sel: ".o_menu_sections .o_nav_entry",                type: "menu"   },

    // ── Product template – Kanban tab ───────────────────────────────────────
    // Odoo 18 (Bootstrap 5) tabs have NO name/href/id attributes.
    // Match all notebook nav-links and filter by text content in isKfmElement.
    {
        sel:      '.o_notebook .nav-link,'
                + '.o_notebook .nav-item a',
        type:     "tab",
        labelSel: null,
    },

    // ── Inventory → Kanban menu (app-switcher level) ─────────────────────
    {
        sel:  '.o_app[data-menu-xmlid*="kanban"],'
            + '.o_app[data-menu-xmlid*="Kanban"]',
        type: "app",
    },

    // ── "Place Order > Scan Kanban" sidebar/action item ──────────────────
    {
        sel:  '.o_menu_sections .o_dropdown_item:is([data-menu-xmlid*="kanban"],[data-menu-xmlid*="Kanban"]),'
            + 'a.o_nav_entry[data-menu-xmlid*="kanban"],'
            + 'a.o_nav_entry[data-menu-xmlid*="Kanban"]',
        type: "menu",
    },

    // ── Buttons added by the module ───────────────────────────────────────
    {
        sel:  'button[name="action_open_kanban"],'
            + 'button[name="kanban_action"],'
            + 'button.o_kanban_for_manufacturing_btn,'
            + '.o_form_view button[name*="kanban"][name*="manufactur"]',
        type: "button",
    },

    // ── Smart buttons (stat buttons) on form views ────────────────────────
    {
        sel:  '.oe_button_box .oe_stat_button[name*="kanban"],'
            + '.oe_button_box .oe_stat_button.kfm_stat_btn',
        type: "button",
    },

    // ── Fields rendered by the module ────────────────────────────────────
    {
        sel:  '.o_field_widget[name="kanban_card_ids"],'
            + '.o_field_widget[name="kfm_route_id"],'
            + '.o_field_widget[name="kfm_replenishment_qty"],'
            + '.o_field_widget[name="kfm_min_qty"],'
            + '.o_field_widget.o_kfm_field',
        type: "field",
    },

    // ── Views / action buttons inside list/form views ────────────────────
    {
        sel:  '.o_action_manager .o_kfm_view,'
            + '.o_view_controller.o_kfm_kanban_view',
        type: "view",
    },
];

// ---------------------------------------------------------------------------
// Expired-subscription dialog
// ---------------------------------------------------------------------------

const EXPIRED_DIALOG_HTML = `
<div id="kfm_expired_dialog_overlay"
     style="position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:99999;
            display:flex;align-items:center;justify-content:center;">
  <div style="background:#fff;border-radius:6px;padding:28px 32px;max-width:440px;
              box-shadow:0 8px 32px rgba(0,0,0,.25);font-family:sans-serif;">
    <h4 style="margin:0 0 12px;font-size:16px;color:#333;">
      <i class="fa fa-lock" style="color:#c0392b;margin-right:8px;"></i>
      Feature Unavailable
    </h4>
    <p style="margin:0 0 20px;color:#555;font-size:14px;line-height:1.5;">
      Your <strong>Kanban for Manufacturing and Kanban Scan</strong> subscription has expired and
      this feature is currently unavailable. Please renew your subscription to
      restore access.
    </p>
    <button id="kfm_expired_dialog_ok"
            style="background:#875a7b;color:#fff;border:none;padding:8px 24px;
                   border-radius:4px;cursor:pointer;font-size:14px;">
      OK
    </button>
  </div>
</div>`;

function showExpiredDialog() {
    if (document.getElementById("kfm_expired_dialog_overlay")) return;
    document.body.insertAdjacentHTML("beforeend", EXPIRED_DIALOG_HTML);
    document.getElementById("kfm_expired_dialog_ok")
        .addEventListener("click", () => {
            document.getElementById("kfm_expired_dialog_overlay")?.remove();
        });
}

// ---------------------------------------------------------------------------
// Helpers – text matching
// ---------------------------------------------------------------------------

function isKfmMenuText(text) {
    return KFM_MENU_TEXTS.some((t) => text === t || text.startsWith(t));
}

function isKfmElement(el, type) {
    // menu, app AND tab all filtered by visible text content
    if (type === "menu" || type === "app" || type === "tab") {
        return isKfmMenuText(el.textContent.trim());
    }
    return true;
}

// ---------------------------------------------------------------------------
// Lock application
// ---------------------------------------------------------------------------

function injectLockIcon(target) {
    if (target.querySelector(".kfm-lock-icon")) return;

    const icon = document.createElement("i");
    icon.className = "fa fa-lock kfm-lock-icon";
    icon.setAttribute("aria-hidden", "true");
    icon.style.cssText = [
        "display:inline-block",
        "font-size:10px",
        "margin-left:4px",
        "vertical-align:middle",
        "position:relative",
        "top:-1px",
        "color:#c0392b",
        "line-height:1",
    ].join(";");

    function findTextOwner(el, depth) {
        if (depth > 3) return null;
        for (const node of el.childNodes) {
            if (node.nodeType === Node.TEXT_NODE && node.textContent.trim()) {
                return el;
            }
        }
        for (const child of el.children) {
            if (child.classList.contains("kfm-lock-icon") || child.classList.contains("fa")) continue;
            const found = findTextOwner(child, depth + 1);
            if (found) return found;
        }
        return null;
    }

    const owner = findTextOwner(target, 0) || target;
    owner.appendChild(icon);
}

function applyLock(el, type = "menu") {
    el.style.opacity       = "0.5";
    el.style.cursor        = "not-allowed";
    el.style.pointerEvents = "auto";

    if (type === "field") {
        el.querySelectorAll("input, select, textarea, button, .o_field_widget")
          .forEach((child) => {
              child.disabled = true;
              child.style.pointerEvents = "none";
          });
    }

    injectLockIcon(el);

    if (!el.dataset.kfmLocked) {
        el.dataset.kfmLocked = "1";
        el.addEventListener(
            "click",
            (e) => {
                e.preventDefault();
                e.stopImmediatePropagation();
                showExpiredDialog();
            },
            true,
        );
    }
}

// ---------------------------------------------------------------------------
// Main scan function
// ---------------------------------------------------------------------------

function lockAllKfmElements() {
    for (const { sel, type, labelSel } of KFM_ELEMENT_SELECTORS) {
        try {
            document.querySelectorAll(sel).forEach((el) => {
                if (!isKfmElement(el, type)) return;

                const lockTarget = labelSel ? el.querySelector(labelSel) ?? el : el;
                applyLock(lockTarget, type);

                if (type === "tab" && el.closest(".nav-item")) {
                    const li = el.closest(".nav-item");
                    li.style.opacity = "0.5";
                    li.style.cursor  = "not-allowed";
                }
            });
        } catch (selectorErr) {
            console.debug("[KFM] Selector skipped:", sel, selectorErr);
        }
    }
}

// ---------------------------------------------------------------------------
// NavBar patch
// ---------------------------------------------------------------------------

patch(NavBar.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");

        onMounted(async () => {
            let isExpired = false;

            try {
                const result = await this.orm.call(
                    "manage.module.api.key",
                    "get_subscription_state_for_module",
                    ["kanban_for_manufacturing"],
                );
                isExpired = result.state === "expired";
            } catch (e) {
                console.warn("[KFM] Could not fetch subscription state:", e);
                return;
            }

            if (!isExpired) return;

            lockAllKfmElements();

            const observer = new MutationObserver(() => lockAllKfmElements());
            observer.observe(document.body, { childList: true, subtree: true });
        });
    },
});
