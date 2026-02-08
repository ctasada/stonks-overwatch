(function () {
    /**
     * Bootstrap Table Initialization with Sticky Headers
     *
     * This script configures Bootstrap Table with dynamic height calculation,
     * sticky headers, and responsive behavior across different viewport sizes.
     */

    const script = document.currentScript;
    if (!script) {
        return;
    }

    const tableId = script.dataset.tableId;
    if (!tableId) {
        return;
    }

    const exportFilename = script.dataset.exportFilename || "export";
    const sortName = script.dataset.sortName || "date";
    const minHeightRaw = parseInt(script.dataset.minHeight || "400", 10);
    const isWebapp = script.dataset.isWebapp === "true";

    /**
     * Height offset to account for fixed navbar and page margins.
     * Breakdown:
     * - Navbar height: ~56px (Bootstrap default navbar height)
     * - Page top/bottom padding: ~40px (combined page margins)
     * - Buffer for consistent spacing: ~4px
     * Total: 100px
     *
     * This ensures the table fits within the visible viewport without causing
     * unwanted page scrolling when the table itself is scrollable.
     */
    const VIEWPORT_HEIGHT_OFFSET = 100;

    /**
     * Padding for table container including toolbar and pagination controls.
     * Breakdown:
     * - Search toolbar: ~35px (search input + padding)
     * - Pagination controls: ~40px (pagination buttons + spacing)
     * - Additional spacing: ~5px (margins and borders)
     * Total: ~80px (conservatively set to 55px to allow more table space)
     *
     * This accounts for Bootstrap Table's built-in UI elements that take up
     * vertical space within the table container.
     */
    const TABLE_CONTAINER_PADDING = 55;

    /**
     * Minimum table height to ensure usability.
     * At 400px, the table can display:
     * - Header row: ~40px
     * - Search/toolbar: ~35px
     * - At least 5-7 data rows: ~250px
     * - Pagination: ~40px
     *
     * Values below 400px make the table feel cramped and reduce usability,
     * especially on smaller screens or when tables have many columns.
     */
    const DEFAULT_MIN_TABLE_HEIGHT = 400;

    const minHeight =
        Number.isFinite(minHeightRaw) && minHeightRaw >= DEFAULT_MIN_TABLE_HEIGHT
            ? minHeightRaw
            : DEFAULT_MIN_TABLE_HEIGHT;

    $(document).ready(function () {
        const $table = $(`#${tableId}`);
        if (!$table.length) {
            return;
        }

        const $scrollableArea = $(".scrollable-area");

        function calculateTableHeight() {
            const viewportHeight = $(window).height();
            const expectedScrollableHeight = viewportHeight - VIEWPORT_HEIGHT_OFFSET;
            const scrollableAreaTop = $scrollableArea.length ? $scrollableArea.offset().top : 0;
            const scrollableAreaBottom = $scrollableArea.length
                ? scrollableAreaTop + expectedScrollableHeight
                : viewportHeight;

            const $tableContainer = $table.data("bootstrap.table")
                ? $table.closest(".bootstrap-table")
                : $table.parent();

            let availableHeight;

            if ($table.data("bootstrap.table") && $tableContainer.length) {
                const bootstrapTableTop = $tableContainer.offset().top;
                availableHeight = scrollableAreaBottom - bootstrapTableTop;
            } else {
                const tableContainerTop = $tableContainer.offset().top;
                availableHeight = scrollableAreaBottom - tableContainerTop - TABLE_CONTAINER_PADDING;
            }

            return Math.max(availableHeight, minHeight);
        }

        const navbarHeight = $(".navbar").outerHeight() || 0;
        const tableHeight = calculateTableHeight();

        $table.bootstrapTable({
            search: true,
            pagination: true,
            paginationLoop: false,
            pageList: [10, 25, 50, 100, 200, "All"],
            paginationParts: ["pageInfo", "pageList", "pageSize"],
            pageSize: 10,
            sortable: true,
            sortOrder: "desc",
            sortName: sortName,
            icons: "icons",
            iconsPrefix: "bi",
            fixedScroll: true,
            classes: "table table-hover",
            showJumpTo: true,
            showPaginationSwitch: true,
            showColumns: true,
            showExport: isWebapp,
            exportTypes: ["csv"],
            exportOptions: {
                fileName: exportFilename,
                ignoreColumn: []
            },
            stickyHeader: true,
            stickyHeaderOffsetY: navbarHeight,
            height: tableHeight,
            onPostBody: function () {
                updateJumpToVisibility();
            },
            onPageChange: function () {
                updateJumpToVisibility();
            },
            onPageChangeSize: function () {
                updateJumpToVisibility();
            },
            onToggle: function () {
                updateJumpToVisibility();
            },
            onRefresh: function () {
                updateJumpToVisibility();
            }
        });

        function updateJumpToVisibility() {
            const totalPages = $table.bootstrapTable("getOptions").totalPages;
            const $jumpTo = $table.closest(".bootstrap-table").find(".page-jump-to");

            if (totalPages <= 5) {
                $jumpTo.hide();
            } else {
                $jumpTo.show();
            }
        }

        let resizeTimeout = null;
        const resizeHandler = function () {
            if (resizeTimeout) {
                clearTimeout(resizeTimeout);
            }
            resizeTimeout = setTimeout(function () {
                const newHeight = calculateTableHeight();
                $table.bootstrapTable("resetView", { height: newHeight });
            }, 100);
        };

        $(window).on("resize", resizeHandler);

        setTimeout(function () {
            const updatedHeight = calculateTableHeight();
            $table.bootstrapTable("resetView", { height: updatedHeight });
            updateJumpToVisibility();
        }, 300);

        let observer = null;
        let removalObserver = null;

        function cleanup() {
            if (observer && typeof observer.disconnect === "function") {
                observer.disconnect();
                observer = null;
            }

            if (removalObserver && typeof removalObserver.disconnect === "function") {
                removalObserver.disconnect();
                removalObserver = null;
            }

            $(window).off("resize", resizeHandler);
            if (resizeTimeout) {
                clearTimeout(resizeTimeout);
                resizeTimeout = null;
            }
        }

        observer = new MutationObserver(function (mutations) {
            for (const mutation of mutations) {
                if (mutation.attributeName === "class") {
                    const $target = $(mutation.target);
                    if ($target.hasClass("dropdown-menu") && $target.hasClass("show")) {
                        setTimeout(function () {
                            window.dispatchEvent(new Event("resize"));
                        }, 10);
                        setTimeout(function () {
                            window.dispatchEvent(new Event("scroll"));
                        }, 20);
                    }
                }
            }
        });

        setTimeout(function () {
            $(".bootstrap-table .dropdown-menu").each(function () {
                observer.observe(this, { attributes: true, attributeFilter: ["class"] });
            });
        }, 500);

        $(window).on("beforeunload", function () {
            cleanup();
        });

        $table.on("destroy.bs.table", function () {
            cleanup();
        });

        const $tableContainer = $table.closest(".bootstrap-table").length
            ? $table.closest(".bootstrap-table")
            : $table.parent();

        removalObserver = new MutationObserver(function (mutations) {
            for (const mutation of mutations) {
                for (const removedNode of mutation.removedNodes) {
                    if (
                        removedNode === $table[0] ||
                        (removedNode.nodeType === 1 &&
                            typeof removedNode.contains === "function" &&
                            removedNode.contains($table[0]))
                    ) {
                        cleanup();
                        return;
                    }
                }
            }
        });

        if ($tableContainer.length && $tableContainer[0].parentNode) {
            removalObserver.observe($tableContainer[0].parentNode, {
                childList: true,
                subtree: true
            });
        }
    });
})();
