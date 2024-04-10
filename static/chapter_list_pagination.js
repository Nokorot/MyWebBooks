
// const entries = [ ];
const rowsPerPage = 10;
const visibleButtonCount = 9;
let pageCount = 1;
let currentPage = -1;

function genereatePageButtons() {
    function genPageButton(idx) {
        const button = document.createElement('a');
        button.innerText = idx;
        button.addEventListener('click', function() {
            showPage(rows, idx);
        });

        const li = document.createElement('li');
        if (idx == currentPage) {
            li.classList.add('page-active');
        }
        li.append(button);

        return li;
    }

    function genEllipsis() {
        const span = document.createElement('span');
        span.innerText = '...';

        const li = document.createElement('li');
        li.classList.add('ellipsis');
        li.append(span);
        return li;
    }

    const pagination = document.getElementById('pagination');
    pagination.innerHTML = '';

    const ul = document.createElement('ul');
    ul.classList.add('pagination');
    pagination.appendChild(ul);


    if (pageCount <= visibleButtonCount) {
        for (let i = 1; i <= pageCount; i++) {
            ul.appendChild(genPageButton(i));
        }
    } else {
        if (currentPage <= Math.ceil(visibleButtonCount / 2)) {
            for (let i = 1; i <= visibleButtonCount - 2; i++) {
                ul.appendChild(genPageButton(i));
            }
            ul.appendChild(genEllipsis());
            ul.appendChild(genPageButton(pageCount));
        } else {
            ul.appendChild(genPageButton(1));
            ul.appendChild(genEllipsis());
            if (currentPage >= pageCount - Math.floor(visibleButtonCount / 2)) {
                for (let i = pageCount - visibleButtonCount + 3; 
                        i <= pageCount; i++) {
                    ul.appendChild(genPageButton(i));
                }
            } else {
                len2 = Math.floor(visibleButtonCount / 4);
                for (let i = currentPage - len2; 
                        i <= currentPage + len2; i++) {
                    ul.appendChild(genPageButton(i));
                }
                ul.appendChild(genEllipsis());
                ul.appendChild(genPageButton(pageCount));
            }
        }
    }
}

function showPage(rows, page) {
    if (currentPage == page)
        return;
    
    currentPage = page;

    const start = (page - 1) * rowsPerPage;
    const end = start + rowsPerPage;

    // First, hide all rows
    Array.from(rows).forEach(row => {
        row.style.display = 'none';
    });

    // Then, show the rows for the current page
    Array.from(rows).slice(start, end).forEach(row => {
        row.style.display = ''; // or 'table-row' if needed
    });

    genereatePageButtons();
}

function initialize(){
    const table = document.getElementById('chapterUrlsTable');
    rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
    pageCount = Math.ceil(rows.length / rowsPerPage);
    
    showPage(rows, 1);
}

// Initialize pagination once the page content is fully loaded
document.addEventListener('DOMContentLoaded', initialize);
