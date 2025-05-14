const token = localStorage.getItem('token');
// If no token, redirect to login page (which is '/' as per main.py)
if (!token) window.location.href = '/';

let userRole = ''; // Store user role globally within this script

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
    localStorage.removeItem('token'); // Clear bad token
    window.location.href = '/'; // Redirect to login
    return null;
  }
}

if (token) {
    const decodedToken = parseJWT(token);
    if (decodedToken && decodedToken.role) {
        userRole = decodedToken.role;
        document.getElementById('userRole').innerText = userRole;

        // Show/hide book creation section based on role
        if (userRole === 'customer') {
            const bookSection = document.getElementById('bookSection');
            if (bookSection) { // Check if element exists
                 bookSection.style.display = 'none';
            }
        }
    } else {
        // Handle case where token is invalid or doesn't contain role
        localStorage.removeItem('token');
        window.location.href = '/';
    }
}


document.getElementById('logoutBtn').addEventListener('click', () => {
  localStorage.removeItem('token');
  window.location.href = '/'; // Redirect to login page
});

// Base API URL prefix (if you standardized in main.py)
// If you did not use /api/v1 in main.py router includes, remove it from paths below.
const API_BASE_URL = '/api/v1';

// Load and display books
async function loadBooks() {
  try {
    // const res = await fetch('/books/', { // Original path
    const res = await fetch(`${API_BASE_URL}/books`, { // Adjusted path if using prefix
      headers: {'Authorization': `Bearer ${token}`}
    });
    if (!res.ok) {
        if (res.status === 401) { // Unauthorized
            localStorage.removeItem('token');
            window.location.href = '/';
        }
        throw new Error(`Failed to load books: ${res.statusText}`);
    }
    const books = await res.json();
    const ul = document.getElementById('bookList');
    if (!ul) return; // Element not found
    ul.innerHTML = ''; // Clear previous list

    books.forEach(b => {
      let li = document.createElement('li');
      li.className = 'list-group-item d-flex justify-content-between align-items-center';
      li.textContent = `ID: ${b.id} - Title: ${b.title} (Publisher ID: ${b.publisher_id || 'N/A'})`; // hgfhghghghghghghghghghghghghghghghg

      let buttonsDiv = document.createElement('div');

      // Only admin/publisher can update/delete books
      if (userRole === 'admin' || userRole === 'publisher') {
        // Update Button
        let updateBtn = document.createElement('button');
        updateBtn.className = 'btn btn-sm btn-info me-2 update-btn';
        updateBtn.textContent = 'Update';
        updateBtn.setAttribute('data-bs-toggle', 'modal');
        updateBtn.setAttribute('data-bs-target', '#updateBookModal');
        updateBtn.setAttribute('data-book-id', b.id);
        updateBtn.setAttribute('data-book-title', b.title);
        updateBtn.setAttribute('data-book-publisher-id', b.publisher_id || ''); // Handle null publisher_id
        buttonsDiv.appendChild(updateBtn);

        // Delete Button
        let deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn-sm btn-danger';
        deleteBtn.textContent = 'Delete';
        deleteBtn.onclick = async () => {
          if (confirm(`Are you sure you want to delete book ID: ${b.id} - ${b.title}?`)) {
            try {
              // const deleteRes = await fetch(`/books/${b.id}`, { // Original path
              const deleteRes = await fetch(`${API_BASE_URL}/books/${b.id}`, { // Adjusted path
                method: 'DELETE',
                headers: {'Authorization': `Bearer ${token}`}
              });
              if (deleteRes.ok) {
                loadBooks(); // Reload books to show changes
              } else {
                const errorData = await deleteRes.json().catch(() => ({detail: "Unknown error during delete."}));
                alert('Failed to delete book: ' + (errorData.detail || deleteRes.statusText));
              }
            } catch (error) {
                console.error('Error deleting book:', error);
                alert('An error occurred while deleting the book.');
            }
          }
        };
        buttonsDiv.appendChild(deleteBtn);
      }
      li.appendChild(buttonsDiv);
      ul.appendChild(li);
    });
  } catch (error) {
    console.error('Error loading books:', error);
    // alert('Could not load books. You might be logged out.');
  }
}

if (token) { // Only load books if token exists
    loadBooks();
}


// Create book form submission (only available if userRole allows)
const createBookForm = document.getElementById('createBookForm');
if (createBookForm) {
    createBookForm.addEventListener('submit', async e => {
        e.preventDefault();
        const title = document.getElementById('bookTitle').value;
        // Ensure publisher_id is treated as a number, or null if empty
        const publisherIdInput = document.getElementById('bookPublisherId').value;
        const publisher_id = publisherIdInput ? parseInt(publisherIdInput, 10) : null;

        if (!title) {
            alert("Book title is required.");
            return;
        }
        // Basic validation for publisher_id if provided
        if (publisherIdInput && isNaN(publisher_id)) {
            alert("Publisher ID must be a number.");
            return;
        }

        try {
            // const res = await fetch('/books/', { // Original path
            const res = await fetch(`${API_BASE_URL}/books`, { // Adjusted path
                method: 'POST',
                headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ title, publisher_id }) // Send publisher_id as null if not provided/valid
            });
            if (res.ok) {
                loadBooks();
                e.target.reset();
            } else {
                const errorData = await res.json().catch(() => ({detail: "Unknown error during book creation."}));
                alert('Could not create book: ' + (errorData.detail || res.statusText));
            }
        } catch (error) {
            console.error('Error creating book:', error);
            alert('An error occurred while creating the book.');
        }
    });
}


// Handle Update Modal population
const updateBookModalElement = document.getElementById('updateBookModal');
if (updateBookModalElement) {
    updateBookModalElement.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget; // Button that triggered the modal
        const bookId = button.getAttribute('data-book-id');
        const bookTitle = button.getAttribute('data-book-title');
        const bookPublisherId = button.getAttribute('data-book-publisher-id');

        const modalTitle = updateBookModalElement.querySelector('.modal-title');
        const modalInputBookId = updateBookModalElement.querySelector('#updateBookId');
        const modalInputTitle = updateBookModalElement.querySelector('#updateBookTitle');
        const modalInputPublisherId = updateBookModalElement.querySelector('#updateBookPublisherId');

        if(modalTitle) modalTitle.textContent = `Update Book ID: ${bookId}`;
        if(modalInputBookId) modalInputBookId.value = bookId;
        if(modalInputTitle) modalInputTitle.value = bookTitle;
        if(modalInputPublisherId) modalInputPublisherId.value = bookPublisherId;
    });
}

// Handle Update Form submission from modal
const updateBookForm = document.getElementById('updateBookForm');
if (updateBookForm) {
    updateBookForm.addEventListener('submit', async e => {
        e.preventDefault();
        const bookId = document.getElementById('updateBookId').value;
        const title = document.getElementById('updateBookTitle').value;
        const publisherIdInput = document.getElementById('updateBookPublisherId').value;
        const publisher_id = publisherIdInput ? parseInt(publisherIdInput, 10) : null;

        const modalInstance = bootstrap.Modal.getInstance(updateBookModalElement);

        if (!title) {
            alert("Book title is required for update.");
            return;
        }
        if (publisherIdInput && isNaN(publisher_id)) {
            alert("Publisher ID must be a number for update.");
            return;
        }

        try {
            // const res = await fetch(`/books/${bookId}`, { // Original path
            const res = await fetch(`${API_BASE_URL}/books/${bookId}`, { // Adjusted path
                method: 'PUT',
                headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ title, publisher_id })
            });

            if (res.ok) {
                alert('Book updated successfully!');
                if(modalInstance) modalInstance.hide();
                loadBooks();
            } else {
                const errorData = await res.json().catch(() => ({detail: "Unknown error during book update."}));
                alert('Failed to update book: ' + (errorData.detail || res.statusText));
            }
        } catch (error) {
            console.error('Error updating book:', error);
            alert('An error occurred while updating the book.');
        }
    });
}