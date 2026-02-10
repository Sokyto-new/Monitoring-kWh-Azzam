// Login page specific JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.querySelector('.login-form');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    
    // Add floating label effect
    [usernameInput, passwordInput].forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            if (!this.value) {
                this.parentElement.classList.remove('focused');
            }
        });
        
        // Check if input has value on page load
        if (input.value) {
            input.parentElement.classList.add('focused');
        }
    });
    
    // Add password visibility toggle
    const passwordGroup = passwordInput.parentElement;
    const toggleBtn = document.createElement('button');
    toggleBtn.type = 'button';
    toggleBtn.className = 'password-toggle';
    toggleBtn.innerHTML = '<i class="fas fa-eye"></i>';
    passwordGroup.appendChild(toggleBtn);
    
    toggleBtn.addEventListener('click', function() {
        const type = passwordInput.type === 'password' ? 'text' : 'password';
        passwordInput.type = type;
        this.innerHTML = type === 'password' 
            ? '<i class="fas fa-eye"></i>' 
            : '<i class="fas fa-eye-slash"></i>';
    });
    
    // Add login form animation
    loginForm.addEventListener('submit', function(e) {
        const submitBtn = this.querySelector('.login-btn');
        if (submitBtn) {
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
            submitBtn.disabled = true;
        }
    });
    
    // Demo credentials autofill
    const demoBtns = document.createElement('div');
    demoBtns.className = 'demo-buttons';
    demoBtns.innerHTML = `
        <button class="demo-btn" data-username="admin" data-password="admin123">
            Use Admin Account
        </button>
        <button class="demo-btn" data-username="budi" data-password="user123">
            Use User Account
        </button>
    `;
    
    loginForm.appendChild(demoBtns);
    
    document.querySelectorAll('.demo-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            usernameInput.value = this.dataset.username;
            passwordInput.value = this.dataset.password;
            
            // Add visual feedback
            this.style.background = 'rgba(41, 98, 255, 0.2)';
            this.style.borderColor = 'var(--accent)';
            
            setTimeout(() => {
                this.style.background = '';
                this.style.borderColor = '';
            }, 1000);
            
            // Auto focus password field
            passwordInput.focus();
        });
    });
    
    // Add styles for new elements
    const style = document.createElement('style');
    style.textContent = `
        .password-toggle {
            position: absolute;
            right: 15px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            color: rgba(255, 255, 255, 0.7);
            cursor: pointer;
            padding: 5px;
            font-size: 1rem;
        }
        
        .password-toggle:hover {
            color: var(--accent);
        }
        
        .form-group {
            position: relative;
        }
        
        .demo-buttons {
            display: flex;
            gap: 10px;
            margin-top: 1.5rem;
            flex-wrap: wrap;
        }
        
        .demo-btn {
            flex: 1;
            min-width: 150px;
            padding: 0.75rem;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 6px;
            color: rgba(255, 255, 255, 0.8);
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 0.9rem;
        }
        
        .demo-btn:hover {
            background: rgba(41, 98, 255, 0.1);
            border-color: var(--accent);
            color: white;
        }
    `;
    document.head.appendChild(style);
});