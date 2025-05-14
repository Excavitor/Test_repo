// const token = localStorage.getItem('token');
// if (!token) window.location.href = '/login';
//
// // decode JWT to read role
// function parseJWT(token) {
//   let base = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
//   let json = atob(base);
//   return JSON.parse(json);
// }
// const { role } = parseJWT(token);
// document.getElementById('userRole').innerText = role;
//
// // show/hide book section: only publisher/admin can create
// if (role === 'customer') {
//   document.getElementById('bookSection').style.display = 'none';
// }
//
// document.getElementById('logoutBtn').onclick = () => {
//   localStorage.removeItem('token');
//   window.location.href = '/login';
// };
//
// // // load and display books
// // async function loadBooks() {
// //   const res = await fetch('/books/', {
// //     headers: {'Authorization': `Bearer ${token}`}
// //   });
// //   const books = await res.json();
// //   const ul = document.getElementById('bookList');
// //   ul.innerHTML = '';
// //   books.forEach(b => {
// //     let li = document.createElement('li');
// //     li.className = 'list-group-item d-flex justify-content-between';
// //     li.textContent = `${b.id}: ${b.title}`;
// //     if (role !== 'customer') {
// //       let btn = document.createElement('button');
// //       btn.className = 'btn btn-sm btn-danger';
// //       btn.textContent = 'Delete';
// //       btn.onclick = async () => {
// //         await fetch(`/books/${b.id}`, {
// //           method: 'DELETE',
// //           headers: {'Authorization': `Bearer ${token}`}
// //         });
// //         loadBooks();
// //       };
// //       li.appendChild(btn);
// //     }
// //     ul.appendChild(li);
// //   });
// // }
//
// // load and display books
// async function loadBooks() {
//   const res = await fetch('/books/', {
//     headers: {'Authorization': `Bearer ${token}`}
//   });
//   const books = await res.json();
//   const ul = document.getElementById('bookList');
//   ul.innerHTML = '';
//   books.forEach(b => {
//     let li = document.createElement('li');
//     li.className = 'list-group-item d-flex justify-content-between align-items-center'; // Added align-items-center for better button alignment
//     li.textContent = `${b.id}: ${b.title}`;
//
//     // Create a div to hold the buttons for better layout
//     let buttonsDiv = document.createElement('div');
//
//     if (role !== 'customer') {
//       // Update Button
//       let updateBtn = document.createElement('button');
//       updateBtn.className = 'btn btn-sm btn-info me-2'; // Added margin to the right
//       updateBtn.textContent = 'Update';
//       updateBtn.onclick = async () => {
//         // Confirmation before updating
//         if (confirm(`Are you sure you want to update book ID: ${b.id}?`)) {
//           // Placeholder for update functionality
//           // You'll need to implement the actual update logic here
//           // For example, prompt the user for new details and make a PUT request
//           const newTitle = prompt("Enter the new title:", b.title);
//           if (newTitle !== null && newTitle.trim() !== "") {
//             // Assuming you have a publisher_id or can prompt for it as well
//             // For simplicity, let's assume publisher_id remains the same or you fetch it
//             // You might need another prompt for publisher_id if it can be changed
//             // const newPublisherId = prompt("Enter the new publisher ID:", b.publisher_id); // You'd need b.publisher_id from the fetched book data
//
//             // Example: Mocking publisher_id if not readily available or updatable here
//             // You should adjust this based on your actual data structure and update requirements
//             const publisherIdToUpdate = b.publisher_id || 1; // Fallback or fetched value
//
//             alert(`Update functionality for book ID: ${b.id} with new title "${newTitle}" to be implemented. Sending to backend...`);
//             // Example of PUT request (ensure your backend /books/{book_id} PUT endpoint expects title and publisher_id)
//             try {
//               const updateRes = await fetch(`/books/${b.id}`, {
//                 method: 'PUT',
//                 headers: {
//                   'Content-Type': 'application/json',
//                   'Authorization': `Bearer ${token}`
//                 },
//                 body: JSON.stringify({ title: newTitle, publisher_id: publisherIdToUpdate }) // Adjust payload as per your schema
//               });
//               if (updateRes.ok) {
//                 alert('Book updated successfully!');
//                 loadBooks(); // Reload books to show changes
//               } else {
//                 const errorData = await updateRes.json();
//                 alert('Failed to update book: ' + (errorData.detail || 'Unknown error'));
//               }
//             } catch (error) {
//               console.error('Error updating book:', error);
//               alert('An error occurred while updating the book.');
//             }
//           }
//         }
//       };
//       buttonsDiv.appendChild(updateBtn); // Add update button to the div
//
//       // Delete Button
//       let deleteBtn = document.createElement('button');
//       deleteBtn.className = 'btn btn-sm btn-danger';
//       deleteBtn.textContent = 'Delete';
//       deleteBtn.onclick = async () => {
//         // Confirmation before deleting
//         if (confirm(`Are you sure you want to delete book ID: ${b.id} - ${b.title}?`)) {
//           await fetch(`/books/${b.id}`, {
//             method: 'DELETE',
//             headers: {'Authorization': `Bearer ${token}`}
//           });
//           loadBooks(); // Reload books to show changes
//         }
//       };
//       buttonsDiv.appendChild(deleteBtn); // Add delete button to the div
//     }
//     li.appendChild(buttonsDiv); // Add the div containing buttons to the list item
//     ul.appendChild(li);
//   });
// }
//
// loadBooks();
//
// // create book
// document.getElementById('createBookForm').addEventListener('submit', async e => {
//   e.preventDefault();
//   const title = document.getElementById('bookTitle').value;
//   const publisher_id = +document.getElementById('bookPublisherId').value;
//   const res = await fetch('/books/', {
//     method: 'POST',
//     headers: {
//       'Content-Type': 'application/json',
//       'Authorization': `Bearer ${token}`
//     },
//     body: JSON.stringify({ title, publisher_id })
//   });
//   if (res.ok) {
//     loadBooks();
//     e.target.reset();
//   } else {
//     alert('Could not create book.');
//   }
// });



const token = localStorage.getItem('token');
if (!token) window.location.href = '/';

// decode JWT to read role
function parseJWT(token) {
  let base = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
  let json = atob(base);
  return JSON.parse(json);
}
const { role } = parseJWT(token);
document.getElementById('userRole').innerText = role;

// show/hide book section: only publisher/admin can create
if (role === 'customer') {
  document.getElementById('bookSection').style.display = 'none';
}

document.getElementById('logoutBtn').onclick = () => {
  localStorage.removeItem('token');
  window.location.href = '/';
};

// load and display books
async function loadBooks() {
  const res = await fetch('/books/', {
    headers: {'Authorization': `Bearer ${token}`}
  });
  const books = await res.json();
  const ul = document.getElementById('bookList');
  ul.innerHTML = '';
  books.forEach(b => {
    let li = document.createElement('li');
    li.className = 'list-group-item d-flex justify-content-between align-items-center';
    li.textContent = `${b.id}: ${b.title}`;

    let buttonsDiv = document.createElement('div');

    if (role !== 'customer') {
      // Update Button
      let updateBtn = document.createElement('button');
      updateBtn.className = 'btn btn-sm btn-info me-2 update-btn';
      updateBtn.textContent = 'Update';
      updateBtn.setAttribute('data-bs-toggle', 'modal');
      updateBtn.setAttribute('data-bs-target', '#updateBookModal');
      updateBtn.setAttribute('data-book-id', b.id);
      updateBtn.setAttribute('data-book-title', b.title);
      updateBtn.setAttribute('data-book-publisher-id', b.publisher_id); // Assuming publisher_id is available
      buttonsDiv.appendChild(updateBtn);

      // Delete Button
      let deleteBtn = document.createElement('button');
      deleteBtn.className = 'btn btn-sm btn-danger';
      deleteBtn.textContent = 'Delete';
      deleteBtn.onclick = async () => {
        if (confirm(`Are you sure you want to delete book ID: ${b.id} - ${b.title}?`)) {
          await fetch(`/books/${b.id}`, {
            method: 'DELETE',
            headers: {'Authorization': `Bearer ${token}`}
          });
          loadBooks();
        }
      };
      buttonsDiv.appendChild(deleteBtn);
    }
    li.appendChild(buttonsDiv);
    ul.appendChild(li);
  });
}

loadBooks();

// create book
document.getElementById('createBookForm').addEventListener('submit', async e => {
  e.preventDefault();
  const title = document.getElementById('bookTitle').value;
  const publisher_id = +document.getElementById('bookPublisherId').value;
  const res = await fetch('/books/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ title, publisher_id })
  });
  if (res.ok) {
    loadBooks();
    e.target.reset();
  } else {
    alert('Could not create book.');
  }
});

// Handle Update Modal show event
const updateBookModal = document.getElementById('updateBookModal');
updateBookModal.addEventListener('show.bs.modal', function (event) {
  const button = event.relatedTarget; // Button that triggered the modal
  const bookId = button.getAttribute('data-book-id');
  const bookTitle = button.getAttribute('data-book-title');
  const bookPublisherId = button.getAttribute('data-book-publisher-id');

  const modalTitle = updateBookModal.querySelector('.modal-title');
  const modalBodyInputTitle = updateBookModal.querySelector('#updateBookTitle');
  const modalBodyInputPublisherId = updateBookModal.querySelector('#updateBookPublisherId');
  const modalBodyInputBookId = updateBookModal.querySelector('#updateBookId');

  modalTitle.textContent = `Update Book ID: ${bookId}`;
  modalBodyInputTitle.value = bookTitle;
  modalBodyInputPublisherId.value = bookPublisherId;
  modalBodyInputBookId.value = bookId;
});

// Handle Update Form submission
document.getElementById('updateBookForm').addEventListener('submit', async e => {
  e.preventDefault();
  const bookId = document.getElementById('updateBookId').value;
  const title = document.getElementById('updateBookTitle').value;
  const publisher_id = +document.getElementById('updateBookPublisherId').value;
  const modal = bootstrap.Modal.getInstance(updateBookModal);

  const res = await fetch(`/books/${bookId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ title, publisher_id })
  });

  if (res.ok) {
    alert('Book updated successfully!');
    modal.hide(); // Hide the modal on success
    loadBooks(); // Reload books to show changes
  } else {
     const errorData = await res.json();
     alert('Failed to update book: ' + (errorData.detail || 'Unknown error'));
  }
});