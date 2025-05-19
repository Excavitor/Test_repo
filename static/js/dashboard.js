// Get the token from localStorage
const token = localStorage.getItem('token');

// If no token is found, redirect the user to the login page
if (!token) {
    window.location.href = '/'; // Redirect to login page (which is '/' as per main.py)
}

// Store the user's role and ID globally within this script
let userRole = '';
let userId = null; // Store user ID from token

// Base API URL prefix (matches the prefix used in main.py for API routers)
const API_BASE_URL = '/api/v1';

// Function to parse the JWT and extract its payload
function parseJWT(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
    return JSON.parse(jsonPayload);
  } catch (e) {
    console.error("Failed to parse JWT:", e);
    localStorage.removeItem('token');
    window.location.href = '/';
    return null;
  }
}

// --- Initial Setup and Role-Based Visibility ---
if (token) {
    const decodedToken = parseJWT(token);
    if (decodedToken && decodedToken.role && decodedToken.user_id) {
        userRole = decodedToken.role;
        userId = decodedToken.user_id; // Get user_id from token
        const userRoleElement = document.getElementById('userRole');
        if (userRoleElement) {
            userRoleElement.innerText = userRole.toUpperCase();
        }

        // Control visibility of sections and forms based on user role
        const createBookForm = document.getElementById('createBookForm');
        if (createBookForm) {
            if (userRole !== 'admin' && userRole !== 'publisher') {
                createBookForm.style.display = 'none';
            }
        }

        const createPublisherForm = document.getElementById('createPublisherForm');
        if (createPublisherForm) {
            if (userRole !== 'admin') {
                createPublisherForm.style.display = 'none';
            }
        }

        const createAuthorForm = document.getElementById('createAuthorForm');
         if (createAuthorForm) {
            if (userRole !== 'admin' && userRole !== 'publisher') {
                createAuthorForm.style.display = 'none';
            }
        }
        // Create review form is visible to all authenticated users.

        loadBooks();
        loadPublishers();
        loadAuthors();
        loadReviews();

    } else {
        console.error("Token invalid or missing role/user_id.");
        localStorage.removeItem('token');
        window.location.href = '/';
    }
}

// --- Logout Functionality ---
const logoutBtn = document.getElementById('logoutBtn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      localStorage.removeItem('token');
      window.location.href = '/';
    });
}

// --- Generic API Request Helper ---
async function fetchApi(url, options = {}) {
    try {
        const headers = {
            'Authorization': `Bearer ${token}`,
            ...options.headers,
        };
        if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(options.body);
        }

        const response = await fetch(`${API_BASE_URL}${url}`, { ...options, headers });

        if (response.status === 401) {
            localStorage.removeItem('token');
            window.location.href = '/';
            throw new Error('Unauthorized: Please log in again.');
        }
         if (response.status === 403) {
             const errorData = await response.json().catch(() => ({ detail: "Forbidden: You do not have permission." }));
             alert('Permission Denied: ' + (errorData.detail || response.statusText));
             throw new Error('Forbidden: Insufficient permissions.');
         }

        if (!response.ok) {
             const errorText = await response.text(); // Use text first, then try JSON
             let errorDetail = `API Error: ${response.status} ${response.statusText}`;
             try {
                const errorData = JSON.parse(errorText);
                errorDetail += ` - ${errorData.detail || 'Unknown error structure'}`;
             } catch (e) {
                errorDetail += ` - ${errorText || 'No additional error detail'}`;
             }
             console.error("API Error Full Response Text:", errorText);
             throw new Error(errorDetail);
        }
        if (response.status === 204) { // No Content
            return null;
        }
        // For DELETE requests that might return a message (like FastAPI default)
        if (options.method === 'DELETE' && response.headers.get("content-type")?.includes("application/json")) {
             return await response.json();
        }
        return await response.json();
    } catch (error) {
        console.error('API Request Failed:', error.message);
        if (!error.message.startsWith('Forbidden')) { // Avoid double alert for 403
            alert(error.message);
        }
        throw error;
    }
}

// Helper function to format date/time
function formatDateTime(dateTimeString) {
    if (!dateTimeString) return 'N/A';
    try {
        // Assuming the backend sends ISO 8601 strings
        const date = new Date(dateTimeString);
         // Check if the date is valid
        if (isNaN(date.getTime())) {
            return 'Invalid Date';
        }
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    } catch (e) {
        console.error("Error formatting date:", dateTimeString, e);
        return 'Invalid Date';
    }
}

// Helper function to truncate text for display
function truncateText(text, maxLength = 100) {
    if (!text) return 'N/A';
    if (text.length > maxLength) {
        return text.substring(0, maxLength) + '...';
    }
    return text;
}

// Function to show full text in a modal
function showDetailsModal(title, content) {
    const modalElement = document.getElementById('viewDetailsModal');
    const modalTitle = modalElement.querySelector('.modal-title');
    const modalBody = modalElement.querySelector('.modal-body');

    modalTitle.textContent = title;
    modalBody.textContent = content || 'No content available.'; // Use textContent to prevent XSS

    const modal = new bootstrap.Modal(modalElement);
    modal.show();
}


// --- Books CRUD ---
async function loadBooks() {
  const table = document.getElementById('bookListTable');
  const tbody = table?.querySelector('tbody');
  if (!tbody) return;
  tbody.innerHTML = '';

  try {
    const books = await fetchApi('/books');
    books.forEach(b => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${b.id}</td>
        <td>${b.title}</td>
        <td>${b.publisher_id || 'N/A'}</td>
        <td>${formatDateTime(b.write_date)}</td> `;
      const actionTd = document.createElement('td');
      if (userRole === 'admin' || userRole === 'publisher') {
        const updateBtn = document.createElement('button');
        updateBtn.className = 'btn btn-sm btn-info me-2';
        updateBtn.textContent = 'Update';
        updateBtn.setAttribute('data-bs-toggle', 'modal');
        updateBtn.setAttribute('data-bs-target', '#updateBookModal');
        updateBtn.setAttribute('data-book-id', b.id);
        updateBtn.setAttribute('data-book-title', b.title);
        updateBtn.setAttribute('data-book-publisher-id', b.publisher_id || '');
        actionTd.appendChild(updateBtn);

        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn-sm btn-danger';
        deleteBtn.textContent = 'Delete';
        deleteBtn.onclick = async () => {
          if (confirm(`Delete book "${b.title}" (ID: ${b.id})?`)) {
            try {
              await fetchApi(`/books/${b.id}`, { method: 'DELETE' });
              loadBooks();
            } catch (error) { /* Handled by fetchApi */ }
          }
        };
        actionTd.appendChild(deleteBtn);
      } else { actionTd.textContent = 'N/A'; }
      tr.appendChild(actionTd);
      tbody.appendChild(tr);
    });
  } catch (error) { /* Handled by fetchApi */ }
}

const createBookForm = document.getElementById('createBookForm');
if (createBookForm) {
    createBookForm.addEventListener('submit', async e => {
        e.preventDefault();
        const title = document.getElementById('bookTitle').value;
        const publisher_id = parseInt(document.getElementById('bookPublisherId').value, 10);
        if (!title || isNaN(publisher_id)) {
            alert("Book title and a valid Publisher ID are required."); return;
        }
        try {
            await fetchApi('/books', { method: 'POST', body: { title, publisher_id } });
            createBookForm.reset(); loadBooks();
        } catch (error) { /* Handled by fetchApi */ }
    });
}

const updateBookModalElement = document.getElementById('updateBookModal');
if (updateBookModalElement) {
    updateBookModalElement.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;
        document.getElementById('updateBookId').value = button.getAttribute('data-book-id');
        document.getElementById('updateBookTitle').value = button.getAttribute('data-book-title');
        document.getElementById('updateBookPublisherId').value = button.getAttribute('data-book-publisher-id');
    });
}

const updateBookForm = document.getElementById('updateBookForm');
if (updateBookForm) {
    updateBookForm.addEventListener('submit', async e => {
        e.preventDefault();
        const id = document.getElementById('updateBookId').value;
        const title = document.getElementById('updateBookTitle').value;
        const publisher_id = parseInt(document.getElementById('updateBookPublisherId').value, 10);
        if (!title || isNaN(publisher_id)) {
            alert("Book title and a valid Publisher ID are required for update."); return;
        }
        try {
            await fetchApi(`/books/${id}`, { method: 'PUT', body: { title, publisher_id } });
            bootstrap.Modal.getInstance(updateBookModalElement).hide();
            loadBooks();
        } catch (error) { /* Handled by fetchApi */ }
    });
}

// --- Publishers CRUD ---
async function loadPublishers() {
  const table = document.getElementById('publisherListTable');
  const tbody = table?.querySelector('tbody');
  if (!tbody) return;
  tbody.innerHTML = '';

  try {
    const publishers = await fetchApi('/publishers'); // Corrected variable name
    publishers.forEach(p => { // Corrected variable name
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${p.id}</td>
        <td>${p.name}</td>
        <td>${p.email}</td>
        <td>${p.phone_number || 'N/A'}</td>
        <td>${p.website || 'N/A'}</td>
        <td>${p.book_count}</td>
        <td>${formatDateTime(p.write_date)}</td> `;
      const actionTd = document.createElement('td');
      if (userRole === 'admin') { // Only admins can update/delete publishers
        const updateBtn = document.createElement('button');
        updateBtn.className = 'btn btn-sm btn-info me-2';
        updateBtn.textContent = 'Update';
        updateBtn.setAttribute('data-bs-toggle', 'modal');
        updateBtn.setAttribute('data-bs-target', '#updatePublisherModal');
        updateBtn.setAttribute('data-publisher-id', p.id);
        updateBtn.setAttribute('data-publisher-name', p.name);
        updateBtn.setAttribute('data-publisher-email', p.email);
        updateBtn.setAttribute('data-publisher-phone', p.phone_number || '');
        updateBtn.setAttribute('data-publisher-website', p.website || '');
        actionTd.appendChild(updateBtn);

        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn-sm btn-danger';
        deleteBtn.textContent = 'Delete';
        deleteBtn.onclick = async () => {
          if (confirm(`Delete publisher "${p.name}" (ID: ${p.id})? This may also delete associated books.`)) {
            try {
              await fetchApi(`/publishers/${p.id}`, { method: 'DELETE' });
              loadPublishers(); loadBooks(); // Reload books as they might be affected
            } catch (error) { /* Handled by fetchApi */ }
          }
        };
        actionTd.appendChild(deleteBtn);
      } else { actionTd.textContent = 'N/A'; }
      tr.appendChild(actionTd);
      tbody.appendChild(tr);
    });
  } catch (error) { /* Handled by fetchApi */ }
}

const createPublisherForm = document.getElementById('createPublisherForm');
if (createPublisherForm) {
    createPublisherForm.addEventListener('submit', async e => {
        e.preventDefault();
        const name = document.getElementById('publisherName').value;
        const email = document.getElementById('publisherEmail').value;
        const phone_number = document.getElementById('publisherPhone').value || null;
        const website = document.getElementById('publisherWebsite').value || null;
        if (!name || !email ) { alert("Publisher name and email are required."); return; }
        try {
            await fetchApi('/publishers', { method: 'POST', body: { name, email, phone_number, website } });
            createPublisherForm.reset(); loadPublishers();
        } catch (error) { /* Handled by fetchApi */ }
    });
}

const updatePublisherModalElement = document.getElementById('updatePublisherModal');
if (updatePublisherModalElement) {
    updatePublisherModalElement.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;
        document.getElementById('updatePublisherId').value = button.getAttribute('data-publisher-id');
        document.getElementById('updatePublisherName').value = button.getAttribute('data-publisher-name');
        document.getElementById('updatePublisherEmail').value = button.getAttribute('data-publisher-email');
        document.getElementById('updatePublisherPhone').value = button.getAttribute('data-publisher-phone');
        document.getElementById('updatePublisherWebsite').value = button.getAttribute('data-publisher-website');
    });
}

const updatePublisherForm = document.getElementById('updatePublisherForm');
if (updatePublisherForm) {
    updatePublisherForm.addEventListener('submit', async e => {
        e.preventDefault();
        const id = document.getElementById('updatePublisherId').value;
        const name = document.getElementById('updatePublisherName').value;
        const email = document.getElementById('updatePublisherEmail').value;
        const phone_number = document.getElementById('updatePublisherPhone').value || null;
        const website = document.getElementById('updatePublisherWebsite').value || null;
        if (!name || !email) { alert("Publisher name and email are required for update."); return; }

        const body = { name, email };
        if(phone_number !== null) body.phone_number = phone_number; // Include null if cleared
        if(website !== null) body.website = website; // Include null if cleared


        try {
            await fetchApi(`/publishers/${id}`, { method: 'PUT', body });
            bootstrap.Modal.getInstance(updatePublisherModalElement).hide();
            loadPublishers();
        } catch (error) { /* Handled by fetchApi */ }
    });
}

// --- Authors CRUD ---
async function loadAuthors() {
  const table = document.getElementById('authorListTable');
  const tbody = table?.querySelector('tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  try {
    const authors = await fetchApi('/authors'); // Corrected variable name
    authors.forEach(a => { // Corrected variable name & iterator
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${a.id}</td>
        <td>${a.name}</td>
        <td>${a.biography ? `<button class="btn btn-sm btn-outline-secondary" onclick="showDetailsModal('Author Biography - ${a.name}', '${a.biography.replace(/'/g, "\\'").replace(/\n/g, '\\n')}')"><i class="fas fa-eye"></i> View</button>` : 'N/A'}</td> <td>${a.birth_date || 'N/A'}</td>
        <td>${a.book_id}</td>
        <td>${formatDateTime(a.write_date)}</td> `;
      const actionTd = document.createElement('td');
      if (userRole === 'admin' || userRole === 'publisher') {
        const updateBtn = document.createElement('button');
        updateBtn.className = 'btn btn-sm btn-info me-2';
        updateBtn.textContent = 'Update';
        updateBtn.setAttribute('data-bs-toggle', 'modal');
        updateBtn.setAttribute('data-bs-target', '#updateAuthorModal');
        updateBtn.setAttribute('data-author-id', a.id);
        updateBtn.setAttribute('data-author-name', a.name);
        updateBtn.setAttribute('data-author-biography', a.biography || '');
        updateBtn.setAttribute('data-author-birth-date', a.birth_date || '');
        // a.book_id is not typically updated via this modal
        actionTd.appendChild(updateBtn);

        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn-sm btn-danger';
        deleteBtn.textContent = 'Delete';
        deleteBtn.onclick = async () => {
          if (confirm(`Delete author "${a.name}" (ID: ${a.id})?`)) {
            try {
              await fetchApi(`/authors/${a.id}`, { method: 'DELETE' });
              loadAuthors();
            } catch (error) { /* Handled by fetchApi */ }
          }
        };
        actionTd.appendChild(deleteBtn);
      } else { actionTd.textContent = 'N/A'; }
      tr.appendChild(actionTd);
      tbody.appendChild(tr);
    });
  } catch (error) { /* Handled by fetchApi */ }
}

const createAuthorForm = document.getElementById('createAuthorForm');
if (createAuthorForm) {
    createAuthorForm.addEventListener('submit', async e => {
        e.preventDefault();
        const name = document.getElementById('authorName').value;
        const biography = document.getElementById('authorBiography').value || null;
        const birth_date = document.getElementById('authorBirthDate').value || null;
        const book_id = parseInt(document.getElementById('authorBookId').value, 10);
        if (!name || isNaN(book_id)) { alert("Author name and a valid Book ID are required."); return; }
        try {
            await fetchApi('/authors', { method: 'POST', body: { name, biography, birth_date, book_id } });
            createAuthorForm.reset(); loadAuthors();
        } catch (error) { /* Handled by fetchApi */ }
    });
}

const updateAuthorModalElement = document.getElementById('updateAuthorModal');
if (updateAuthorModalElement) {
    updateAuthorModalElement.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;
        document.getElementById('updateAuthorId').value = button.getAttribute('data-author-id');
        document.getElementById('updateAuthorName').value = button.getAttribute('data-author-name');
        document.getElementById('updateAuthorBiography').value = button.getAttribute('data-author-biography');
        document.getElementById('updateAuthorBirthDate').value = button.getAttribute('data-author-birth-date');
    });
}

const updateAuthorForm = document.getElementById('updateAuthorForm');
if (updateAuthorForm) {
    updateAuthorForm.addEventListener('submit', async e => {
        e.preventDefault();
        const id = document.getElementById('updateAuthorId').value;
        const name = document.getElementById('updateAuthorName').value;
        const biography = document.getElementById('updateAuthorBiography').value || null;
        const birth_date = document.getElementById('updateAuthorBirthDate').value || null;
        if (!name) { alert("Author name is required for update."); return;}

        const body = { name }; // Start with required fields
        // Only include optional fields if they are not null or empty strings
        if (biography !== null) body.biography = biography;
        if (birth_date !== null) body.birth_date = birth_date;
        // book_id is not updated here

        try {
            await fetchApi(`/authors/${id}`, { method: 'PUT', body });
            bootstrap.Modal.getInstance(updateAuthorModalElement).hide();
            loadAuthors();
        } catch (error) { /* Handled by fetchApi */ }
    });
}

// --- Reviews CRUD ---
async function loadReviews() {
  const table = document.getElementById('reviewListTable');
  const tbody = table?.querySelector('tbody');
  if (!tbody) return;
  tbody.innerHTML = '';

  try {
    const reviews = await fetchApi('/reviews');
    reviews.forEach(r => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${r.id}</td>
        <td>${r.book_id}</td>
        <td>${r.rating}</td>
        <td>${r.review_text ? `<button class="btn btn-sm btn-outline-secondary" onclick="showDetailsModal('Review Text (ID: ${r.id})', '${r.review_text.replace(/'/g, "\\'").replace(/\n/g, '\\n')}')"><i class="fas fa-eye"></i> View</button>` : 'N/A'}</td> <td>${r.user_id}</td>
        <td>${formatDateTime(r.date_posted)}</td> <td>${formatDateTime(r.write_date)}</td> `;
      const actionTd = document.createElement('td');
      // Only review owner or admin can update/delete
      if (userRole === 'admin' || (userId && userId === r.user_id)) {
        const updateBtn = document.createElement('button');
        updateBtn.className = 'btn btn-sm btn-info me-2';
        updateBtn.textContent = 'Update';
        updateBtn.setAttribute('data-bs-toggle', 'modal');
        updateBtn.setAttribute('data-bs-target', '#updateReviewModal');
        updateBtn.setAttribute('data-review-id', r.id);
        updateBtn.setAttribute('data-review-rating', r.rating);
        updateBtn.setAttribute('data-review-text', r.review_text || '');
        actionTd.appendChild(updateBtn);

        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn-sm btn-danger';
        deleteBtn.textContent = 'Delete';
        deleteBtn.onclick = async () => {
          if (confirm(`Delete review ID ${r.id}?`)) {
            try {
              await fetchApi(`/reviews/${r.id}`, { method: 'DELETE' });
              loadReviews();
            } catch (error) { /* Handled by fetchApi */ }
          }
        };
        actionTd.appendChild(deleteBtn);
      } else { actionTd.textContent = 'N/A'; }
      tr.appendChild(actionTd);
      tbody.appendChild(tr);
    });
  } catch (error) { /* Handled by fetchApi */ }
}

const createReviewForm = document.getElementById('createReviewForm');
if (createReviewForm) {
    createReviewForm.addEventListener('submit', async e => {
        e.preventDefault();
        const book_id = parseInt(document.getElementById('reviewBookId').value, 10);
        const rating = parseInt(document.getElementById('reviewRating').value, 10);
        const review_text = document.getElementById('reviewText').value || null;
        if (isNaN(book_id) || isNaN(rating) || rating < 1 || rating > 5) {
            alert("A valid Book ID and Rating (1-5) are required."); return;
        }
        try {
            await fetchApi('/reviews', { method: 'POST', body: { book_id, rating, review_text } });
            createReviewForm.reset(); loadReviews();
        } catch (error) { /* Handled by fetchApi */ }
    });
}

const updateReviewModalElement = document.getElementById('updateReviewModal');
if (updateReviewModalElement) {
    updateReviewModalElement.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;
        document.getElementById('updateReviewId').value = button.getAttribute('data-review-id');
        document.getElementById('updateReviewRating').value = button.getAttribute('data-review-rating');
        document.getElementById('updateReviewText').value = button.getAttribute('data-review-text');
    });
}

const updateReviewForm = document.getElementById('updateReviewForm');
if (updateReviewForm) {
    updateReviewForm.addEventListener('submit', async e => {
        e.preventDefault();
        const id = document.getElementById('updateReviewId').value;
        const rating = parseInt(document.getElementById('updateReviewRating').value, 10);
        const review_text = document.getElementById('updateReviewText').value || null;
        if (isNaN(rating) || rating < 1 || rating > 5) {
            alert("Rating must be a number between 1 and 5 for update."); return;
        }
        const body = { rating };
        if(review_text !== null) body.review_text = review_text; // Include null if cleared

        try {
            await fetchApi(`/reviews/${id}`, { method: 'PUT', body });
            bootstrap.Modal.getInstance(updateReviewModalElement).hide();
            loadReviews();
        } catch (error) { /* Handled by fetchApi */ }
    });
}
