/**
 * Table Filters Module
 *
 * Provides reusable AJAX-based table filtering functionality.
 * Features:
 * - Debounced search input
 * - Instant dropdown filtering
 * - URL state management (bookmarkable filters)
 * - Loading states
 * - Error handling
 *
 * Usage:
 *   const tableFilter = new TableFilter({
 *     tableBodyId: 'usersTableBody',
 *     apiEndpoint: '/api/v1/api/users',
 *     filters: {
 *       search: { element: '#searchInput', param: 'search', debounce: true },
 *       status: { element: '#statusFilter', param: 'status' },
 *       role: { element: '#roleFilter', param: 'role_id' }
 *     },
 *     renderRow: (item) => `<tr>...</tr>`,
 *     onError: (error) => showFlashMessage(error, 'error', false)
 *   });
 */

class TableFilter {
  constructor(options) {
    this.tableBodyId = options.tableBodyId;
    this.apiEndpoint = options.apiEndpoint;
    this.filters = options.filters || {};
    this.renderRow = options.renderRow;
    this.renderEmpty = options.renderEmpty || this.defaultRenderEmpty.bind(this);
    this.onError = options.onError || console.error;
    this.onBeforeFetch = options.onBeforeFetch || (() => {});
    this.onAfterFetch = options.onAfterFetch || (() => {});
    this.debounceDelay = options.debounceDelay || 300;
    this.paginationContainerId = options.paginationContainerId || null;
    this.renderPagination = options.renderPagination || null;
    this.colSpan = options.colSpan || 7;

    // Internal state
    this.debounceTimers = {};
    this.currentRequest = null;
    this.isLoading = false;

    // Initialize
    this.init();
  }

  init() {
    // Set up filter event listeners
    Object.keys(this.filters).forEach(key => {
      const filter = this.filters[key];
      const element = document.querySelector(filter.element);

      if (!element) {
        console.warn(`TableFilter: Element not found for filter "${key}": ${filter.element}`);
        return;
      }

      if (filter.debounce) {
        // Debounced input (for search fields)
        element.addEventListener('input', (e) => {
          this.handleDebouncedInput(key, e.target.value);
        });

        // Also handle Enter key for immediate search
        element.addEventListener('keypress', (e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            this.clearDebounce(key);
            this.fetchAndRender();
          }
        });
      } else {
        // Immediate filter (for dropdowns)
        element.addEventListener('change', () => {
          this.fetchAndRender();
        });
      }
    });

    // Handle browser back/forward
    window.addEventListener('popstate', () => {
      this.syncFiltersFromURL();
      this.fetchAndRender(false); // Don't update URL on popstate
    });

    // Sync filters from URL on initial load (if there are URL params)
    if (window.location.search) {
      this.syncFiltersFromURL();
    }
  }

  handleDebouncedInput(key, value) {
    this.clearDebounce(key);
    this.debounceTimers[key] = setTimeout(() => {
      this.fetchAndRender();
    }, this.debounceDelay);
  }

  clearDebounce(key) {
    if (this.debounceTimers[key]) {
      clearTimeout(this.debounceTimers[key]);
      this.debounceTimers[key] = null;
    }
  }

  clearAllDebounce() {
    Object.keys(this.debounceTimers).forEach(key => {
      this.clearDebounce(key);
    });
  }

  collectFilterValues() {
    const values = {};

    Object.keys(this.filters).forEach(key => {
      const filter = this.filters[key];
      const element = document.querySelector(filter.element);

      if (element) {
        const value = element.value.trim();
        if (value) {
          values[filter.param] = value;
        }
      }
    });

    return values;
  }

  buildQueryString(params) {
    const searchParams = new URLSearchParams();

    Object.keys(params).forEach(key => {
      if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
        searchParams.set(key, params[key]);
      }
    });

    return searchParams.toString();
  }

  updateURL(params) {
    const queryString = this.buildQueryString(params);
    const newURL = queryString
      ? `${window.location.pathname}?${queryString}`
      : window.location.pathname;

    window.history.pushState({ filters: params }, '', newURL);
  }

  syncFiltersFromURL() {
    const urlParams = new URLSearchParams(window.location.search);

    Object.keys(this.filters).forEach(key => {
      const filter = this.filters[key];
      const element = document.querySelector(filter.element);
      const urlValue = urlParams.get(filter.param) || '';

      if (element) {
        element.value = urlValue;
      }
    });
  }

  showLoading() {
    this.isLoading = true;
    const tableBody = document.getElementById(this.tableBodyId);

    if (tableBody) {
      // Add loading overlay
      const loadingRow = document.createElement('tr');
      loadingRow.id = 'tableLoadingRow';
      loadingRow.innerHTML = `
        <td colspan="${this.colSpan}" class="px-4 py-12 text-center">
          <div class="flex flex-col items-center justify-center">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-3"></div>
            <span class="text-gray-500 dark:text-gray-400">Loading...</span>
          </div>
        </td>
      `;

      // Fade out existing content
      tableBody.style.opacity = '0.5';
      tableBody.style.pointerEvents = 'none';
    }
  }

  hideLoading() {
    this.isLoading = false;
    const tableBody = document.getElementById(this.tableBodyId);
    const loadingRow = document.getElementById('tableLoadingRow');

    if (loadingRow) {
      loadingRow.remove();
    }

    if (tableBody) {
      tableBody.style.opacity = '1';
      tableBody.style.pointerEvents = 'auto';
    }
  }

  defaultRenderEmpty() {
    return `
      <tr>
        <td colspan="${this.colSpan}" class="px-4 py-12 text-center">
          <div class="flex flex-col items-center justify-center text-gray-500 dark:text-gray-400">
            <i class="fas fa-search text-4xl mb-3 opacity-50"></i>
            <p class="text-lg font-medium">No results found</p>
            <p class="text-sm">Try adjusting your search or filter criteria</p>
          </div>
        </td>
      </tr>
    `;
  }

  async fetchAndRender(updateURLState = true) {
    // Abort any pending request
    if (this.currentRequest) {
      this.currentRequest.abort();
    }

    const controller = new AbortController();
    this.currentRequest = controller;

    const params = this.collectFilterValues();

    // Update URL if requested
    if (updateURLState) {
      this.updateURL(params);
    }

    this.showLoading();
    this.onBeforeFetch();

    try {
      const queryString = this.buildQueryString(params);
      const url = queryString
        ? `${this.apiEndpoint}?${queryString}`
        : this.apiEndpoint;

      const response = await fetch(url, {
        signal: controller.signal,
        headers: {
          'Accept': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      this.renderTable(data);

      // Render pagination if configured
      if (this.paginationContainerId && this.renderPagination) {
        const paginationContainer = document.getElementById(this.paginationContainerId);
        if (paginationContainer) {
          paginationContainer.innerHTML = this.renderPagination(data);
        }
      }

      this.onAfterFetch(data);

    } catch (error) {
      if (error.name === 'AbortError') {
        // Request was aborted, ignore
        return;
      }

      console.error('TableFilter fetch error:', error);
      this.onError('Failed to load data. Please try again.');

    } finally {
      this.hideLoading();
      this.currentRequest = null;
    }
  }

  renderTable(data) {
    const tableBody = document.getElementById(this.tableBodyId);

    if (!tableBody) {
      console.error(`TableFilter: Table body not found: ${this.tableBodyId}`);
      return;
    }

    // Handle different response formats
    const items = data.data || data.items || data;

    if (!Array.isArray(items) || items.length === 0) {
      tableBody.innerHTML = this.renderEmpty();
      return;
    }

    const html = items.map(item => this.renderRow(item)).join('');
    tableBody.innerHTML = html;

    // Re-attach any event listeners needed for action buttons
    this.attachRowEventListeners();
  }

  attachRowEventListeners() {
    // Override this method in page-specific implementation if needed
    // This is called after rendering to re-attach click handlers, etc.
  }

  clearFilters() {
    // Clear all filter inputs
    Object.keys(this.filters).forEach(key => {
      const filter = this.filters[key];
      const element = document.querySelector(filter.element);

      if (element) {
        element.value = '';
      }
    });

    // Clear URL and fetch
    this.fetchAndRender();
  }

  refresh() {
    this.fetchAndRender(false);
  }
}

// Utility function for debouncing (standalone, for use outside the class)
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Export for module systems (if used)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { TableFilter, debounce };
}
