// handle both login & registration
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');

if (loginForm) {
  loginForm.addEventListener('submit', async e => {
    e.preventDefault();
    const username = e.target.username.value;
    const password = e.target.password.value;

    const res = await fetch('/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: new URLSearchParams({username, password})
    });
    const data = await res.json();
    if (res.ok) {
      localStorage.setItem('token', data.access_token);
      window.location.href = '/dashboard';
    } else {
      alert('Login failed: ' + data.detail);
    }
  });
}

if (registerForm) {
  registerForm.addEventListener('submit', async e => {
    e.preventDefault();
    const payload = {
      username: e.target.username.value,
      password: e.target.password.value,
      role: e.target.role.value
    };
    const res = await fetch('/register/', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      alert('Registered! Please log in.');
      window.location.href = '/';
    } else {
      const err = await res.json();
      alert('Registration error: ' + err.detail);
    }
  });
}
