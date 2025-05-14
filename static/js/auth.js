const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');

if (loginForm) {
  loginForm.addEventListener('submit', async e => {
    e.preventDefault();
    const username = e.target.username.value;
    const password = e.target.password.value;

    try {
      // const res = await fetch('/login', { // Path should match main.py POST /login
      const res = await fetch('/login', { // Corrected in main.py to /login
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: new URLSearchParams({username, password})
      });
      const data = await res.json();
      if (res.ok) {
        localStorage.setItem('token', data.access_token);
        window.location.href = '/dashboard'; // Redirect to dashboard
      } else {
        alert('Login failed: ' + (data.detail || 'Unknown error'));
      }
    } catch (error) {
        console.error('Login request failed:', error);
        alert('Login request failed. Please try again.');
    }
  });
}

if (registerForm) {
  registerForm.addEventListener('submit', async e => {
    e.preventDefault();
    const payload = {
      username: e.target.username.value,
      password: e.target.password.value,
      role: e.target.role.value // Ensure 'role' field exists and is correctly populated
    };

    try {
      // const res = await fetch('/register/', { // Path should match main.py POST /register
      const res = await fetch('/register', { // Corrected in main.py to /register (no trailing slash)
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        // const data = await res.json(); // Optional: use registered user data if needed
        alert('Registered successfully! Please log in.');
        window.location.href = '/'; // Redirect to login page (which is '/')
      } else {
        const err = await res.json();
        alert('Registration error: ' + (err.detail || 'Unknown error'));
      }
    } catch (error) {
        console.error('Registration request failed:', error);
        alert('Registration request failed. Please try again.');
    }
  });
}