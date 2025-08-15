/**
 * Transforms old table-based quote structures into new div-based quote structures
 * Handles nested quotes recursively
 */
function transformQuotes() {
    // Transform quotes in the entire document
    transformQuotesInDOM(document);
}

/**
 * Transforms a single quote table into the new structure
 * @param {HTMLElement} table - The table element to transform
 */
function transformSingleQuote(table) {
    // Skip if this table has already been processed or doesn't exist
    if (!table || !table.parentNode || !table.classList.contains('classicquote')) {
        return;
    }
    
    // Extract the author name from the first cell
    const authorCell = table.querySelector('tr:first-child td span.genmed b');
    if (!authorCell) return;
    
    // Extract full author text (including " a écrit:")
    const fullAuthorText = authorCell.textContent.trim();
    
    // Extract the quote content from the second row
    const quoteCell = table.querySelector('tr:nth-child(2) td.quote');
    if (!quoteCell) return;
    
    let quoteContent = quoteCell.innerHTML;
    
    // Check if this quote contains nested quotes that need the "load more" functionality
    const hasNestedQuotes = quoteContent.includes('class="realquote"');
    
    if (hasNestedQuotes) {
        // Add the "load more" button before the first nested quote
        quoteContent = quoteContent.replace(
            /<div class="realquote">/,
            '<div class="quoteloadmore" onclick="jQuery(this).parent().find(\'.realquote\').removeClass(\'realquote\'); jQuery(this).parent().find(\'.quoteloadmore\').remove();"><i style="opacity: 0.3" class="fa-solid fa-chevrons-down"></i></div><div class="realquote">'
        );
    }
    
    // Create the new quote structure
    const newQuoteDiv = document.createElement('div');
    newQuoteDiv.className = 'realquote';
    
    const blockquote = document.createElement('blockquote');
    blockquote.setAttribute('style', `--quote-suffix: &quot;${fullAuthorText}&quot;`);
    
    const cite = document.createElement('cite');
    
    // Add the author text as plain text (no span wrapper)
    cite.textContent = fullAuthorText;
    
    const contentDiv = document.createElement('div');
    contentDiv.innerHTML = quoteContent;
    
    // Build the structure
    blockquote.appendChild(cite);
    blockquote.appendChild(contentDiv);
    newQuoteDiv.appendChild(blockquote);
    
    // Replace the old table with the new structure
    table.parentNode.replaceChild(newQuoteDiv, table);
}

/**
 * Alternative function that processes HTML string directly
 * @param {string} htmlString - The HTML string to process
 * @returns {string} - The transformed HTML string
 */
function transformQuotesInString(htmlString) {
    // Create a temporary container to work with the HTML
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = htmlString;
    
    // Apply the transformation to the temporary container
    transformQuotesInDOM(tempDiv);
    
    return tempDiv.innerHTML;
}

/**
 * Transforms quotes in a given DOM element (used by both main function and string function)
 * @param {HTMLElement} container - The container element to search for quotes
 */
function transformQuotesInDOM(container) {
    // Transform quotes recursively, starting from the deepest nested ones
    transformQuotesRecursivelyInContainer(container);
}

/**
 * Recursively transforms quotes in a container, processing nested quotes first
 * @param {HTMLElement} container - The container element to search for quotes
 */
function transformQuotesRecursivelyInContainer(container) {
    // Find all tables with class "classicquote" in the container
    const classicQuotes = container.querySelectorAll('table.classicquote');
    
    if (classicQuotes.length === 0) return;
    
    // Convert NodeList to Array and sort by nesting depth (deepest first)
    const quotesArray = Array.from(classicQuotes);
    quotesArray.sort((a, b) => {
        const depthA = getQuoteNestingDepth(a);
        const depthB = getQuoteNestingDepth(b);
        return depthB - depthA; // Sort in descending order (deepest first)
    });
    
    // Transform quotes from deepest to shallowest
    quotesArray.forEach(table => {
        transformSingleQuote(table);
    });
    
    // Check if there are still quotes to transform (in case some were added during transformation)
    const remainingQuotes = container.querySelectorAll('table.classicquote');
    if (remainingQuotes.length > 0) {
        transformQuotesRecursivelyInContainer(container);
    }
}

/**
 * Get the nesting depth of a quote table (how many parent quote tables it has)
 * @param {HTMLElement} table - The table element to check
 * @returns {number} - The nesting depth
 */
function getQuoteNestingDepth(table) {
    let depth = 0;
    let parent = table.parentElement;
    
    while (parent) {
        if (parent.tagName === 'TABLE' && parent.classList.contains('classicquote')) {
            depth++;
        }
        parent = parent.parentElement;
    }
    
    return depth;
}

// Auto-transform quotes when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    transformQuotes();
});

// Also transform quotes when new content is dynamically added
const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === Node.ELEMENT_NODE) {
                    // Check if the added node contains classic quotes
                    const quotes = node.querySelectorAll ? node.querySelectorAll('table.classicquote') : [];
                    if (quotes.length > 0 || (node.classList && node.classList.contains('classicquote'))) {
                        setTimeout(() => transformQuotesInDOM(node), 0);
                    }
                }
            });
        }
    });
});

// Start observing
observer.observe(document.body, {
    childList: true,
    subtree: true
});

// Export functions for manual use
window.transformQuotes = transformQuotes;
window.transformQuotesInString = transformQuotesInString;
