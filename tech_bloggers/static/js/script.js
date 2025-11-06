document.addEventListener("DOMContentLoaded", () => {
  // Note: TinyMCE will handle font styling for content textarea
  // The summary textarea will use the CSS rules we've already defined

  // Hamburger Menu Toggle
  const hamburger = document.getElementById("hamburger");
  const navMenu = document.getElementById("nav-menu");
  
  if (hamburger && navMenu) {
    hamburger.addEventListener("click", () => {
      hamburger.classList.toggle("active");
      navMenu.classList.toggle("active");
    });
    
    // Close menu when clicking on a link
    const navLinks = navMenu.querySelectorAll("a");
    navLinks.forEach(link => {
      link.addEventListener("click", () => {
        hamburger.classList.remove("active");
        navMenu.classList.remove("active");
      });
    });
  }

  // Removed js-init-hidden reveal to avoid empty content before JS executes
  // Auto-hide messages after 5 seconds
  const messages = document.querySelector(".messages");
  if (messages) {
    setTimeout(() => {
      messages.style.opacity = "0";
      messages.style.transform = "translateX(-100%)";
      
      setTimeout(() => {
        messages.remove();
      }, 500); // Animation duration
    }, 5000); // Hide delay
  }

  // Settings Page Tabs
  const settingsTabs = document.querySelectorAll(".settings-tab");
  if (settingsTabs.length > 0) {
    settingsTabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        // Update tabs
        settingsTabs.forEach((t) => t.classList.remove("active"));
        tab.classList.add("active");

        // Update panels
        const panels = document.querySelectorAll(".tab-panel");
        panels.forEach((p) => p.classList.remove("active"));
        document
          .getElementById(`${tab.dataset.tab}-panel`)
          .classList.add("active");

        // Save active tab to session storage
        sessionStorage.setItem("activeSettingsTab", tab.dataset.tab);
      });
    });

    // Restore active tab on page load
    const activeTab = sessionStorage.getItem("activeSettingsTab");
    if (activeTab) {
      const tab = document.querySelector(`[data-tab="${activeTab}"]`);
      if (tab) tab.click();
    }
  }

    // Avatar Upload
    const avatarInput = document.getElementById("avatar-input");
    const avatarPlaceholder = document.getElementById("avatar-placeholder");
    const uploadZone = document.getElementById("avatar-upload-zone");

    // Old simple behavior: only preview and drag & drop (no drag-center)

    if (avatarInput && uploadZone) {
      // Handle file selection
      avatarInput.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (file && file.type.startsWith("image/")) {
          const reader = new FileReader();
          reader.onload = (e) => {
            // Update preview image
            const previewImg = document.getElementById("avatar-preview-img");
            if (previewImg) {
              previewImg.src = e.target.result;
            } else {
              if (avatarPlaceholder) {
                avatarPlaceholder.style.display = "none";
              }
              const img = document.createElement("img");
              img.id = "avatar-preview-img";
              img.src = e.target.result;
              img.alt = "Profile avatar";
              uploadZone.insertBefore(img, uploadZone.firstChild);
            }
            // Reset offset when new image is uploaded
            const offsetXInput = document.getElementById('avatar-offset-x');
            const offsetYInput = document.getElementById('avatar-offset-y');
            if (offsetXInput) offsetXInput.value = '0';
            if (offsetYInput) offsetYInput.value = '0';
            
            // Re-initialize drag-to-reposition functionality
            setTimeout(() => {
              initAvatarDragReposition();
            }, 100);
          };
          reader.readAsDataURL(file);
        }
      });

    // Handle drag and drop
    ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
      uploadZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
      });
    });

    ["dragenter", "dragover"].forEach((eventName) => {
      uploadZone.addEventListener(eventName, () => {
        uploadZone.classList.add("drag-over");
      });
    });

    ["dragleave", "drop"].forEach((eventName) => {
      uploadZone.addEventListener(eventName, () => {
        uploadZone.classList.remove("drag-over");
      });
    });

    uploadZone.addEventListener("drop", (e) => {
      const file = e.dataTransfer.files[0];
      if (file && file.type.startsWith("image/")) {
        avatarInput.files = e.dataTransfer.files;
        const reader = new FileReader();
        reader.onload = (e) => {
          // Update preview image
          const previewImg = document.getElementById("avatar-preview-img");
          if (previewImg) {
            previewImg.src = e.target.result;
          } else {
            if (avatarPlaceholder) {
              avatarPlaceholder.style.display = "none";
            }
            const img = document.createElement("img");
            img.id = "avatar-preview-img";
            img.src = e.target.result;
            img.alt = "Profile avatar";
            uploadZone.insertBefore(img, uploadZone.firstChild);
          }
          // Reset offset when new image is uploaded via drag-drop
          const offsetXInput = document.getElementById('avatar-offset-x');
          const offsetYInput = document.getElementById('avatar-offset-y');
          if (offsetXInput) offsetXInput.value = '0';
          if (offsetYInput) offsetYInput.value = '0';
          
          // Re-initialize drag-to-reposition functionality
          setTimeout(() => {
            initAvatarDragReposition();
          }, 100);
        };
        reader.readAsDataURL(file);
      }
    });

    // Change Avatar button handler
    const changeAvatarBtn = document.getElementById('change-avatar-btn');
    if (changeAvatarBtn) {
      changeAvatarBtn.addEventListener('click', () => {
        avatarInput.click();
      });
    }
    
    // Also allow clicking on placeholder when no image exists
    if (avatarPlaceholder) {
      avatarPlaceholder.addEventListener('click', () => {
        avatarInput.click();
      });
    }
  }

  // ====================================
  // Avatar Drag-to-Reposition Functionality
  // ====================================
  let avatarWasDragged = false; // Track if avatar was dragged to prevent upload trigger
  
  function initAvatarDragReposition() {
    const avatarImg = document.getElementById('avatar-preview-img');
    const container = document.getElementById('avatar-upload-zone');
    
    if (!avatarImg || !container) return;
    
    let isDragging = false;
    let hasMoved = false; // Track if mouse actually moved during drag
    let startX, startY, mouseDownTime;
    let currentX = 0, currentY = 0;
    
    // Check if there are saved position values
    let offsetXInput = document.getElementById('avatar-offset-x');
    let offsetYInput = document.getElementById('avatar-offset-y');
    
    // Create hidden inputs if they don't exist
    if (!offsetXInput) {
      offsetXInput = document.createElement('input');
      offsetXInput.type = 'hidden';
      offsetXInput.name = 'avatar_offset_x';
      offsetXInput.id = 'avatar-offset-x';
      offsetXInput.value = '0';
      container.appendChild(offsetXInput);
    }
    
    if (!offsetYInput) {
      offsetYInput = document.createElement('input');
      offsetYInput.type = 'hidden';
      offsetYInput.name = 'avatar_offset_y';
      offsetYInput.id = 'avatar-offset-y';
      offsetYInput.value = '0';
      container.appendChild(offsetYInput);
    }
    
    // Load saved position if exists
    currentX = parseFloat(offsetXInput.value) || 0;
    currentY = parseFloat(offsetYInput.value) || 0;
    
    // Apply initial position immediately
    if (currentX !== 0 || currentY !== 0) {
      avatarImg.style.transform = `translate(calc(-50% + ${currentX}px), calc(-50% + ${currentY}px))`;
    }
    
    // Apply initial position
    updateImagePosition();
    
    // Make image draggable (prevent default image drag behavior)
    avatarImg.style.cursor = 'move';
    avatarImg.draggable = false;
    
    function updateImagePosition() {
      // Combine centering transform with drag offset
      avatarImg.style.transform = `translate(calc(-50% + ${currentX}px), calc(-50% + ${currentY}px))`;
      avatarImg.style.transition = isDragging ? 'none' : 'transform 0.2s ease';
      
      // Update hidden inputs
      offsetXInput.value = currentX;
      offsetYInput.value = currentY;
    }
    
    // ALWAYS block clicks directly on the image - image is ONLY for dragging
    avatarImg.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();
      return false;
    }, true);
    
    // Mouse events for dragging
    avatarImg.addEventListener('mousedown', function(e) {
      e.preventDefault(); // Prevent image selection
      e.stopPropagation(); // Don't bubble to upload zone
      
      isDragging = true;
      hasMoved = false;
      mouseDownTime = Date.now();
      startX = e.clientX - currentX;
      startY = e.clientY - currentY;
      
      avatarImg.style.cursor = 'grabbing';
    });
    
    document.addEventListener('mousemove', function(e) {
      if (!isDragging) return;
      
      e.preventDefault();
      
      const newX = e.clientX - startX;
      const newY = e.clientY - startY;
      
      // Check if mouse actually moved from mousedown position (more than 5px threshold)
      const deltaX = Math.abs(e.clientX - (startX + currentX));
      const deltaY = Math.abs(e.clientY - (startY + currentY));
      
      if (deltaX > 5 || deltaY > 5) {
        hasMoved = true;
        avatarWasDragged = true; // Set immediately when drag detected
      }
      
      // Apply constraints - preview is 250px, allow proportional movement
      const maxOffset = 90; // Maximum pixels the image can be offset (will be scaled server-side)
      currentX = Math.max(-maxOffset, Math.min(maxOffset, newX));
      currentY = Math.max(-maxOffset, Math.min(maxOffset, newY));
      
      updateImagePosition();
    });
    
    document.addEventListener('mouseup', function(e) {
      if (isDragging) {
        const mouseUpTime = Date.now();
        const wasQuickClick = (mouseUpTime - mouseDownTime) < 200;
        
        isDragging = false;
        avatarImg.style.cursor = 'move';
        
        // Update position
        updateImagePosition();
        
        // Only block subsequent clicks if it was an actual drag (not a quick click)
        if (hasMoved && !wasQuickClick) {
          setTimeout(() => {
            avatarWasDragged = false;
            hasMoved = false;
          }, 500);
        } else {
          // Reset immediately for quick clicks
          avatarWasDragged = false;
          hasMoved = false;
        }
      }
    });
    
    // Touch events for mobile
    avatarImg.addEventListener('touchstart', function(e) {
      e.stopPropagation(); // Prevent triggering upload zone events
      
      isDragging = true;
      hasMoved = false;
      mouseDownTime = Date.now();
      const touch = e.touches[0];
      startX = touch.clientX - currentX;
      startY = touch.clientY - currentY;
    }, { passive: true });
    
    document.addEventListener('touchmove', function(e) {
      if (!isDragging) return;
      
      const touch = e.touches[0];
      const newX = touch.clientX - startX;
      const newY = touch.clientY - startY;
      
      // Check if touch actually moved from touchstart position
      const deltaX = Math.abs(touch.clientX - (startX + currentX));
      const deltaY = Math.abs(touch.clientY - (startY + currentY));
      
      if (deltaX > 5 || deltaY > 5) {
        hasMoved = true;
        avatarWasDragged = true; // Set immediately when drag detected
      }
      
      // Apply constraints - preview is 250px, allow proportional movement
      const maxOffset = 90; // Maximum pixels the image can be offset (will be scaled server-side)
      currentX = Math.max(-maxOffset, Math.min(maxOffset, newX));
      currentY = Math.max(-maxOffset, Math.min(maxOffset, newY));
      
      updateImagePosition();
    }, { passive: true });
    
    document.addEventListener('touchend', function() {
      if (isDragging) {
        isDragging = false;
        
        // Update position to scale back down smoothly
        updateImagePosition();
        
        // Reset flag after delay (already set in touchmove if drag occurred)
        if (hasMoved) {
          setTimeout(() => {
            avatarWasDragged = false;
          }, 500);
        }
      }
    });
  }
  
  // Initialize drag functionality if avatar image exists on page load
  if (document.getElementById('avatar-preview-img')) {
    initAvatarDragReposition();
  }

  // Password Toggle
  const passwordToggles = document.querySelectorAll(".password-toggle");
  if (passwordToggles.length > 0) {
    passwordToggles.forEach((toggle) => {
      toggle.addEventListener("click", () => {
        const input = document.getElementById(toggle.dataset.target);
        const icon = toggle.querySelector("i");

        if (input.type === "password") {
          input.type = "text";
          icon.classList.remove("fa-eye");
          icon.classList.add("fa-eye-slash");
        } else {
          input.type = "password";
          icon.classList.remove("fa-eye-slash");
          icon.classList.add("fa-eye");
        }
      });
    });
  }

  // Password Requirements (supports signup and reset-confirm forms)
  const newPasswordInput =
    document.getElementById("new_password1") ||
    document.getElementById("id_new_password1") ||
    document.getElementById("id_password1");
  const confirmPasswordInput =
    document.getElementById("new_password2") ||
    document.getElementById("id_new_password2") ||
    document.getElementById("id_password2");
  if (newPasswordInput && confirmPasswordInput) {
    const requirements = {
      length: (password) => password.length >= 8,
      uppercase: (password) => /[A-Z]/.test(password),
      lowercase: (password) => /[a-z]/.test(password),
      number: (password) => /[0-9]/.test(password),
      special: (password) => /[^A-Za-z0-9]/.test(password),
    };

    const updateRequirements = (password) => {
      Object.entries(requirements).forEach(([key, validate]) => {
        const item = document.querySelector(`[data-requirement="${key}"]`);
        const icon = item.querySelector("i");

        if (validate(password)) {
          item.classList.add("valid");
          item.classList.remove("invalid");
          icon.classList.remove("fa-times");
          icon.classList.add("fa-check");
        } else {
          item.classList.add("invalid");
          item.classList.remove("valid");
          icon.classList.remove("fa-check");
          icon.classList.add("fa-times");
        }
      });
    };

    newPasswordInput.addEventListener("input", (e) => {
      updateRequirements(e.target.value);
    });

    confirmPasswordInput.addEventListener("input", (e) => {
      const match = e.target.value === newPasswordInput.value;
      const feedback = confirmPasswordInput.parentElement.querySelector(".form-feedback");

      if (feedback) {
        feedback.remove();
      }

      if (e.target.value && !match) {
        const div = document.createElement("div");
        div.className = "form-feedback error";
        div.textContent = "Passwords do not match";
        confirmPasswordInput.parentElement.appendChild(div);
      }
    });
  }

  // Sign Up form real-time validation
  const signupForm = document.getElementById("signup-form");
  if (signupForm) {
    const usernameInput = document.getElementById("id_username");
    const emailInput = document.getElementById("id_email");
    const signupPassword1 = document.getElementById("id_password1");
    const signupPassword2 = document.getElementById("id_password2");

    const setFieldError = (inputEl, message) => {
      const group = inputEl && inputEl.closest && inputEl.closest(".form-group");
      const feedback = group ? group.querySelector(".form-feedback") : null;
      if (feedback) {
        feedback.textContent = message || "";
        feedback.classList.toggle("error", !!message);
      }
      if (message) inputEl.classList.add("error");
      else inputEl.classList.remove("error");
    };

    const validateUsername = () => {
      if (!usernameInput) return true;
      const value = usernameInput.value.trim();
      let msg = "";
      if (value.length < 5) msg = "At least 5 characters";
      else if (value.length > 30) msg = "Max 30 characters";
      else if (!/^[A-Za-z0-9_]+$/.test(value)) msg = "Use letters, numbers, or underscores only";
      setFieldError(usernameInput, msg);
      return !msg;
    };

    const validateEmail = () => {
      if (!emailInput) return true;
      const value = emailInput.value.trim();
      let msg = "";
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(value)) msg = "Enter a valid email";
      setFieldError(emailInput, msg);
      return !msg;
    };

    const requirements = {
      length: (password) => password.length >= 8,
      uppercase: (password) => /[A-Z]/.test(password),
      lowercase: (password) => /[a-z]/.test(password),
      number: (password) => /[0-9]/.test(password),
      special: (password) => /[^A-Za-z0-9]/.test(password),
    };

    const updateSignupRequirements = (password) => {
      Object.entries(requirements).forEach(([key, validate]) => {
        const item = signupForm.querySelector(`[data-requirement="${key}"]`);
        if (!item) return;
        const icon = item.querySelector("i");
        if (validate(password)) {
          item.classList.add("valid");
          item.classList.remove("invalid");
          if (icon) {
            icon.classList.remove("fa-times");
            icon.classList.add("fa-check");
          }
        } else {
          item.classList.add("invalid");
          item.classList.remove("valid");
          if (icon) {
            icon.classList.remove("fa-check");
            icon.classList.add("fa-times");
          }
        }
      });
    };

    const validatePasswordMatch = () => {
      if (!signupPassword1 || !signupPassword2) return true;
      const match = signupPassword2.value === signupPassword1.value;
      const group = signupPassword2.closest(".form-group");
      const feedback = group ? group.querySelector(".form-feedback") : null;
      if (feedback) {
        const showError = signupPassword2.value && !match;
        feedback.textContent = showError ? "Passwords do not match" : "";
        feedback.classList.toggle("error", showError);
      }
      if (signupPassword2.value && !match) signupPassword2.classList.add("error");
      else signupPassword2.classList.remove("error");
      return match;
    };

    if (usernameInput) {
      usernameInput.addEventListener("input", validateUsername);
      usernameInput.addEventListener("blur", validateUsername);
    }
    if (emailInput) {
      emailInput.addEventListener("input", validateEmail);
      emailInput.addEventListener("blur", validateEmail);
    }
    if (signupPassword1) {
      signupPassword1.addEventListener("input", (e) => updateSignupRequirements(e.target.value));
    }
    if (signupPassword2) {
      signupPassword2.addEventListener("input", validatePasswordMatch);
    }

    signupForm.addEventListener("submit", (e) => {
      const a = validateUsername();
      const b = validateEmail();
      updateSignupRequirements(signupPassword1 ? signupPassword1.value : "");
      const c = validatePasswordMatch();
      if (!a || !b || !c) {
        e.preventDefault();
        // Focus the first invalid field
        if (!a && usernameInput) usernameInput.focus();
        else if (!b && emailInput) emailInput.focus();
        else if (!c && signupPassword2) signupPassword2.focus();
      }
    });
  }

  // Blog Post Image Upload
  const uploadImageBtn = document.getElementById("uploadImage");
  const imageInput = document.getElementById("image");
  const imagePreview = document.getElementById("imagePreview");

  if (uploadImageBtn && imageInput) {
    // Click the hidden file input when the upload button is clicked
    uploadImageBtn.addEventListener("click", () => {
      imageInput.click();
    });

    // Handle file selection and preview
    imageInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (file && file.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onload = (e) => {
          // Update preview image
          imagePreview.innerHTML = `<img src="${e.target.result}" alt="Post image preview" />`;
        };
        reader.readAsDataURL(file);
      }
    });
  }

  // Ensure TinyMCE content is saved before form submission
  const createPostForm = document.querySelector('.create-post-form');
  if (createPostForm) {
    createPostForm.addEventListener('submit', function() {
      if (window.tinymce && window.tinymce.get('id_content')) {
        window.tinymce.get('id_content').save();
      }
    });
  }

  // Search Clear Functionality (All Posts page)
  const searchInput = document.getElementById('search-input');
  const searchIcon = document.getElementById('search-icon');
  const searchButton = document.getElementById('search-button');
  
  if (searchInput && searchIcon && searchButton) {
    let isEnterPressed = false;
    
    // Check if user has searched in this session
    let hasSearched = sessionStorage.getItem('hasSearched') === 'true';
    
    function updateSearchIcon() {
      if (hasSearched && searchInput.value.trim() !== '') {
        // Show clear icon (X) only after user has searched
        searchIcon.className = 'fas fa-times';
        searchButton.title = 'Clear search';
      } else {
        // Show search icon
        searchIcon.className = 'fas fa-search';
        searchButton.title = 'Search';
      }
    }
    
    // Update icon on page load
    updateSearchIcon();
    
    // Handle Enter key press
    searchInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        isEnterPressed = true;
        hasSearched = true;
        sessionStorage.setItem('hasSearched', 'true');
        // Let the form submit normally
      }
    });
    
    // Handle button click
    searchButton.addEventListener('click', function(e) {
      if (isEnterPressed) {
        // If Enter was pressed, don't handle the button click
        isEnterPressed = false;
        return;
      }
      
      if (hasSearched && searchInput.value.trim() !== '') {
        // If user has searched and there's text, clear it instead of submitting
        e.preventDefault();
        searchInput.value = '';
        hasSearched = false;
        sessionStorage.removeItem('hasSearched');
        searchInput.focus();
        updateSearchIcon();
      } else {
        // If no text or hasn't searched yet, perform search
        hasSearched = true;
        sessionStorage.setItem('hasSearched', 'true');
        // Let the form submit normally
      }
    });
    
    // Update icon when user types
    searchInput.addEventListener('input', function() {
      updateSearchIcon();
    });
  }

  // Search Clear Functionality (Manage Posts page)
  const manageSearchInput = document.getElementById('manage-search-input');
  const manageSearchButton = document.getElementById('manage-search-button');
  const manageSearchIcon = manageSearchButton ? manageSearchButton.querySelector('i') : null;
  
  if (manageSearchInput && manageSearchIcon && manageSearchButton) {
    let isEnterPressed = false;
    
    // Check if user has searched in this session
    let hasSearched = sessionStorage.getItem('manageHasSearched') === 'true';
    
    function updateManageSearchIcon() {
      if (hasSearched && manageSearchInput.value.trim() !== '') {
        // Show clear icon (X) only after user has searched
        manageSearchIcon.className = 'fas fa-times';
        manageSearchButton.title = 'Clear search';
      } else {
        // Show search icon
        manageSearchIcon.className = 'fas fa-search';
        manageSearchButton.title = 'Search';
      }
    }
    
    // Update icon on page load
    updateManageSearchIcon();
    
    // Handle Enter key press
    manageSearchInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        isEnterPressed = true;
        hasSearched = true;
        sessionStorage.setItem('manageHasSearched', 'true');
        // Let the form submit normally
      }
    });
    
    // Handle button click
    manageSearchButton.addEventListener('click', function(e) {
      if (isEnterPressed) {
        // If Enter was pressed, don't handle the button click
        isEnterPressed = false;
        return;
      }
      
      if (hasSearched && manageSearchInput.value.trim() !== '') {
        // If user has searched and there's text, clear it instead of submitting
        e.preventDefault();
        manageSearchInput.value = '';
        hasSearched = false;
        sessionStorage.removeItem('manageHasSearched');
        manageSearchInput.focus();
        updateManageSearchIcon();
      } else {
        // If no text or hasn't searched yet, perform search
        hasSearched = true;
        sessionStorage.setItem('manageHasSearched', 'true');
        // Let the form submit normally
      }
    });
    
    // Update icon when user types
    manageSearchInput.addEventListener('input', function() {
      updateManageSearchIcon();
    });
  }

  // No extra submit/focus persistence needed in simplified mode

  // Like Button Functionality
  const likeButton = document.querySelector('.like-btn');
  if (likeButton) {
    likeButton.addEventListener('click', function(e) {
      e.preventDefault();
      
      const postId = this.dataset.postId;
      const postSlug = this.dataset.postSlug;
      const isLiked = this.dataset.liked === 'true';
      
      // Disable button during request
      this.disabled = true;
      this.style.opacity = '0.6';
      
      // Get CSRF token
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                       document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
      
      // Make AJAX request
      fetch(`/blog/${postId}-${postSlug}/like/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({})
      })
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
          // Update button state
          const heartIcon = this.querySelector('i');
          const likeText = this.querySelector('.like-text');
          
          if (data.liked) {
            // Post is now liked
            this.classList.add('active');
            heartIcon.className = 'fas fa-heart';
            likeText.textContent = 'Unlike';
            this.dataset.liked = 'true';
          } else {
            // Post is now unliked
            this.classList.remove('active');
            heartIcon.className = 'far fa-heart';
            likeText.textContent = 'Like';
            this.dataset.liked = 'false';
          }
        } else {
          console.error('Error liking post:', data);
        }
      })
      .catch(error => {
        console.error('Error:', error);
      })
      .finally(() => {
        // Re-enable button
        this.disabled = false;
        this.style.opacity = '1';
      });
    });
  }

  // Comment Reply Functionality
  const replyButtons = document.querySelectorAll('.btn-reply');
  replyButtons.forEach(button => {
    button.addEventListener('click', function(e) {
      e.preventDefault();
      
      const commentId = this.dataset.commentId;
      const replyForm = document.getElementById(`reply-form-${commentId}`);
      
      if (replyForm) {
        // Hide all other reply forms
        document.querySelectorAll('.reply-form').forEach(form => {
          if (form.id !== `reply-form-${commentId}`) {
            form.style.display = 'none';
          }
        });
        
        // Toggle current reply form
        if (replyForm.style.display === 'none') {
          replyForm.style.display = 'block';
          replyForm.querySelector('textarea').focus();
        } else {
          replyForm.style.display = 'none';
        }
      }
    });
  });

  // Cancel Reply Functionality
  const cancelReplyButtons = document.querySelectorAll('.cancel-reply');
  cancelReplyButtons.forEach(button => {
    button.addEventListener('click', function(e) {
      e.preventDefault();
      
      const commentId = this.dataset.commentId;
      const replyForm = document.getElementById(`reply-form-${commentId}`);
      
      if (replyForm) {
        replyForm.style.display = 'none';
        // Clear the textarea
        replyForm.querySelector('textarea').value = '';
      }
    });
  });

  // Tag Selection Functionality - Simplified Toggle
  const tagSelector = document.querySelector('.tag-selector');
  if (tagSelector) {
    const availableTagsList = document.getElementById('available-tags-list');
    const hiddenInput = document.getElementById('tags-hidden-input');
    
    let selectedTags = [];
    const MAX_TAGS = 3;

    // Initialize with existing selected tags (for edit mode)
    function initializeSelectedTags() {
      const existingTags = hiddenInput.value ? hiddenInput.value.split(',') : [];
      if (existingTags.length > 0) {
        existingTags.forEach(tagId => {
          const tagElement = availableTagsList.querySelector(`[data-tag-id="${tagId.trim()}"]`);
          if (tagElement) {
            toggleTag(tagElement);
          }
        });
      }
    }

    function updateAvailableTagsState() {
      const count = selectedTags.length;
      
      // Update available tags state
      const availableTags = availableTagsList.querySelectorAll('.available-tag');
      availableTags.forEach(tag => {
        const tagId = tag.dataset.tagId;
        const isSelected = selectedTags.some(t => t.id === tagId);
        
        if (isSelected) {
          tag.classList.add('selected');
          tag.classList.remove('disabled');
        } else if (count >= MAX_TAGS) {
          tag.classList.add('disabled');
          tag.classList.remove('selected');
        } else {
          tag.classList.remove('selected', 'disabled');
        }
      });
    }

    function updateHiddenInput() {
      hiddenInput.value = selectedTags.map(tag => tag.id).join(',');
    }

    function toggleTag(tagElement) {
      const tagId = tagElement.dataset.tagId;
      const tagName = tagElement.dataset.tagName;
      const isCurrentlySelected = selectedTags.some(t => t.id === tagId);

      if (isCurrentlySelected) {
        // Deselect tag
        selectedTags = selectedTags.filter(tag => tag.id !== tagId);
      } else {
        // Select tag (only if under limit)
        if (selectedTags.length >= MAX_TAGS) return;
        
        // Add to selected tags (alphabetically sorted)
        selectedTags.push({ id: tagId, name: tagName });
        selectedTags.sort((a, b) => a.name.localeCompare(b.name));
      }

      updateAvailableTagsState();
      updateHiddenInput();
    }

    // Add click handlers to available tags
    const availableTags = availableTagsList.querySelectorAll('.available-tag');
    availableTags.forEach(tag => {
      tag.addEventListener('click', function() {
        if (!this.classList.contains('disabled')) {
          toggleTag(this);
        }
      });
    });

    // Initialize
    initializeSelectedTags();
    updateAvailableTagsState();
  }

  // WYSIWYG Editor will be implemented here in the future
  // TinyMCE initialization (only on create/edit post pages)
  const shouldUseTinyMCE = !!window.__USE_TINYMCE_FOR_CONTENT__;
  const contentTextarea = document.getElementById('id_content') || document.querySelector('textarea[name="content"]');

  if (shouldUseTinyMCE && contentTextarea) {
    const initTiny = () => {
      if (!window.tinymce || !window.tinymce.init) return false;

      // Remove any previous instance (e.g., back/forward cache)
      try {
        if (window.tinymce.get('id_content')) {
          window.tinymce.get('id_content').remove();
        }
      } catch (e) {}

      // Avoid native form validation on the hidden textarea
      try { contentTextarea.removeAttribute('required'); } catch(e) {}

      window.tinymce.init({
        selector: '#id_content',
        license_key: 'gpl',
        skin: 'oxide-dark',
        content_css: [
          'dark',
          // Load site stylesheets inside editor iframe so content matches dark theme
          (document.querySelector('link[rel="stylesheet"][href*="/static/css/base.css"]')?.href),
          (document.querySelector('link[rel="stylesheet"][href*="/static/css/components.css"]')?.href),
          (document.querySelector('link[rel="stylesheet"][href*="/static/css/pages/blog.css"]')?.href),
          (document.querySelector('link[rel="stylesheet"][href*="/static/css/vendors/tinymce.css"]')?.href),
          (document.querySelector('link[rel="stylesheet"][href*="/static/css/responsive.css"]')?.href)
        ].filter(Boolean), // Remove any undefined entries
        height: 450,
        menubar: false,
        statusbar: false,
        plugins: 'lists link table image',
        toolbar: 'undo redo | bold italic underline | alignleft aligncenter alignright alignjustify | bullist numlist | blockquote | customcode | link | image | table',
        // Table styling options - simplified
        table_default_attributes: {
          border: '1'
        },
        table_default_styles: {
          'border-collapse': 'collapse',
          'border': '1px solid #ccc'
        },
        // Simplified table properties - only Width, Height, Alignment
        table_appearance_options: false,
        table_advtab: false,
        table_cell_advtab: false,
        table_row_advtab: false,
        // Allow basic table sizing with clear units
        table_style_by_css: true,
        // Force inline styles instead of classes
        inline_styles: true,
        convert_urls: false,
        // Improve table navigation and editing
        table_tab_navigation: true,
        table_use_colgroups: false,
        // Set font styling for editor content
        content_style: `
          body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
            font-size: 1rem !important;
            line-height: 1.6 !important;
            color: #c9d1d9 !important;
            background: #0d1117 !important;
          }
          p {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
            font-size: 1rem !important;
          }
        `,
        valid_elements: 'p,br,hr,div,b,i,u,em,strong,span[style],a[href|title|rel|target],ul,ol,li,blockquote,code,pre,img[src|alt|title|width|height],h1,h2,h3,font[face|size|color|style],table[style|border|cellpadding|cellspacing],thead,tbody,tr,th[style|colspan|rowspan],td[style|colspan|rowspan]',
        valid_styles: {
          '*': 'color,background-color,font-family,font-size,font-weight,font-style,text-decoration,text-align,line-height,width,height,border,border-collapse,border-spacing,padding,margin,margin-left,margin-right,margin-top,margin-bottom,float'
        },
        // Ensure styles are preserved
        forced_root_block: 'p',
        force_br_newlines: false,
        branding: false,
        default_link_target: '_blank',
        link_default_protocol: 'https',
        link_no_follow: true,
        // Image upload configuration - upload immediately but track for cleanup
        images_upload_url: '/blog/upload-image/',
        images_upload_handler: function (blobInfo, success, failure) {
          // Upload the image immediately
          const formData = new FormData();
          formData.append('file', blobInfo.blob(), blobInfo.filename());
          
          // Get CSRF token
          const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
          
          return fetch('/blog/upload-image/', {
            method: 'POST',
            body: formData,
            headers: {
              'X-CSRFToken': csrfToken
            }
          })
          .then(response => {
            if (!response.ok) {
              return response.json().then(data => {
                throw new Error(data.error || `Server error: ${response.status}`);
              });
            }
            return response.json();
          })
          .then(data => {
            if (data.location) {
              // Store the uploaded URL for potential cleanup
              if (!window.uploadedImages) {
                window.uploadedImages = [];
              }
              window.uploadedImages.push(data.location);
              
                        // Set this as the current image URL for the dialog
                        if (window.currentImageDialog) {
                          window.currentImageUrl = data.location;
                        }
              
              if (typeof success === 'function') {
                success(data.location);
              }
              return data.location;
            } else {
              const errorMessage = 'Upload failed: ' + (data.error || 'Unknown error');
              if (typeof failure === 'function') {
                failure(errorMessage);
              }
              throw new Error(errorMessage);
            }
          })
          .catch(error => {
            if (typeof failure === 'function') {
              failure(error.message);
            }
            throw error;
          });
        },
        // Base64 image pasting is blocked server-side by bleach (no data: protocol)
        setup: (editor) => {
          // Ensure proper font styling when editor initializes
          editor.on('init', () => {
            const body = editor.getBody();
            if (body) {
              body.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';
              body.style.fontSize = '1rem';
              body.style.lineHeight = '1.6';
            }
          });
          
          // Add custom code block button
          editor.ui.registry.addButton('customcode', {
            text: 'Code',
            tooltip: 'Insert Code Block',
            onAction: function() {
              const selectedText = editor.selection.getContent();
              let codeContent = selectedText;
              
              if (!codeContent) {
                codeContent = '// Enter your code here'; 
              }
              
              // Create code block using TinyMCE's DOM methods
              const preElement = editor.dom.create('pre', {
                'class': 'code-block'
              });
              const codeElement = editor.dom.create('code', {}, codeContent);
              preElement.appendChild(codeElement);
              
              // Insert the code block
              editor.selection.setNode(preElement);
              
              // Add a paragraph after for cursor positioning
              const paragraph = editor.dom.create('p', {}, '<br>');
              editor.dom.insertAfter(paragraph, preElement);
              
              // Set cursor after the code block
              setTimeout(function() {
                editor.selection.setCursorLocation(editor.getBody(), editor.getBody().childNodes.length);
              }, 100);
            }
          });
          
          // Ensure tables get default styling when created
          editor.on('ExecCommand', function(e) {
            if (e.command === 'mceInsertTable') {
              setTimeout(function() {
                const tables = editor.dom.select('table');
                tables.forEach(function(table) {
                  if (!table.getAttribute('style')) {
                    editor.dom.setStyle(table, 'border-collapse', 'collapse');
                    editor.dom.setStyle(table, 'border', '1px solid #ccc');
                  }
                  const cells = editor.dom.select('td, th', table);
                  cells.forEach(function(cell, index) {
                    if (!cell.getAttribute('style')) {
                      editor.dom.setStyle(cell, 'border', '1px solid #ccc');
                      editor.dom.setStyle(cell, 'padding', '8px');
                    }
                    // Ensure all cells are editable and have proper content
                    if (!cell.textContent || cell.textContent.trim() === '') {
                      cell.innerHTML = '<br data-mce-bogus="1">';
                    }
                    // Fix for last column header navigation issue
                    // Add a non-breaking space to ensure cell is always editable
                    if (cell.nodeName === 'TH' && cell.innerHTML === '<br data-mce-bogus="1">') {
                      cell.innerHTML = '&nbsp;';
                    }
                    // Ensure cell is properly set as contenteditable
                    cell.setAttribute('contenteditable', 'true');
                  });
                  
                  // Automatically insert a paragraph after the table for spacing
                  const nextSibling = table.nextSibling;
                  if (!nextSibling || nextSibling.nodeName !== 'P') {
                    const paragraph = editor.dom.create('p', {}, '<br>');
                    editor.dom.insertAfter(paragraph, table);
                  }
                });
              }, 100);
            }
          });
          
          // Fix table header navigation issues - ensure all cells are properly editable
          editor.on('NodeChange', function(e) {
            if (e.element.nodeName === 'TABLE' || editor.dom.getParent(e.element, 'table')) {
              const table = e.element.nodeName === 'TABLE' ? e.element : editor.dom.getParent(e.element, 'table');
              const headers = editor.dom.select('th', table);
              headers.forEach(function(th) {
                // Ensure header has content for cursor placement
                if (!th.textContent || th.textContent.trim() === '') {
                  th.innerHTML = '&nbsp;';
                }
              });
            }
          });
          
          // Track image dialog using MutationObserver approach
          window.currentImageDialog = null;
          window.currentImageUrl = null;
          let dialogConfirmed = false;
          
          // Watch for dialog appearance/disappearance
          const dialogObserver = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
              if (mutation.type === 'childList') {
                // Check if image dialog appeared
                const imageDialogs = document.querySelectorAll('.tox-dialog');
                imageDialogs.forEach(function(dialog) {
                  const dialogTitle = dialog.querySelector('.tox-dialog__title');
                  if (dialogTitle && dialogTitle.textContent.toLowerCase().includes('image')) {
                        if (!window.currentImageDialog) {
                          window.currentImageDialog = dialog;
                          window.currentImageUrl = null;
                          dialogConfirmed = false;
                      
                      // Watch for image selection - try multiple approaches
                      const srcInput = dialog.querySelector('input[name="src"]');
                      if (srcInput) {
                        // Set initial value if it exists
                        if (srcInput.value) {
                          window.currentImageUrl = srcInput.value;
                        }
                        
                        // Watch for value changes
                        const inputObserver = new MutationObserver(function() {
                          if (srcInput.value && srcInput.value !== window.currentImageUrl) {
                            window.currentImageUrl = srcInput.value;
                          }
                        });
                        inputObserver.observe(srcInput, { attributes: true, attributeFilter: ['value'] });
                        
                        // Also listen for input events
                        srcInput.addEventListener('input', function() {
                          if (this.value && this.value !== window.currentImageUrl) {
                            window.currentImageUrl = this.value;
                          }
                        });
                        
                        // Also listen for change events
                        srcInput.addEventListener('change', function() {
                          if (this.value && this.value !== window.currentImageUrl) {
                            window.currentImageUrl = this.value;
                          }
                        });
                      }
                      
                      // Watch for OK button clicks - try multiple selectors
                      const okButton = dialog.querySelector('button[type="submit"], .tox-button--primary, button[aria-label*="OK"], button[aria-label*="ok"], button[title*="OK"], button[title*="ok"]');
                      if (okButton) {
                        okButton.addEventListener('click', function() {
                          dialogConfirmed = true;
                        });
                      } else {
                        // Try to find any button that might be OK
                        const allButtons = dialog.querySelectorAll('button');
                        allButtons.forEach(function(btn, index) {
                          const text = btn.textContent.toLowerCase();
                          const ariaLabel = btn.getAttribute('aria-label')?.toLowerCase() || '';
                          const title = btn.getAttribute('title')?.toLowerCase() || '';
                          
                          if (text.includes('ok') || text.includes('save') || text.includes('insert') || 
                              ariaLabel.includes('ok') || ariaLabel.includes('save') || ariaLabel.includes('insert') ||
                              title.includes('ok') || title.includes('save') || title.includes('insert')) {
                            btn.addEventListener('click', function() {
                              dialogConfirmed = true;
                            });
                          }
                        });
                      }
                    }
                  }
                });
                
                // Check if dialog disappeared
                if (window.currentImageDialog && !document.contains(window.currentImageDialog)) {
                  // If dialog was cancelled and we have an uploaded image, delete it
                  if (!dialogConfirmed && window.currentImageUrl && window.uploadedImages && window.uploadedImages.includes(window.currentImageUrl)) {
                    // Remove from our tracking list
                    window.uploadedImages = window.uploadedImages.filter(url => url !== window.currentImageUrl);
                    
                    // Delete the image from server
                    fetch('/blog/delete-image/', {
                      method: 'POST',
                      body: JSON.stringify({ url: window.currentImageUrl }),
                      headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('input[name="csrfmiddlewaretoken"]')?.value
                      }
                    })
                    .then(response => response.json())
                    .then(data => {
                      // Image deletion handled silently
                    })
                    .catch(error => {
                      // Error handling silent for production
                    });
                  }
                  
                  window.currentImageDialog = null;
                  window.currentImageUrl = null;
                  dialogConfirmed = false;
                }
              }
            });
          });
          
          // Start observing for dialog changes
          dialogObserver.observe(document.body, {
            childList: true,
            subtree: true
          });
          
          // Add unit hints to table properties dialog using MutationObserver
          const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
              if (mutation.type === 'childList') {
                // Look for TinyMCE dialogs that have been added
                const dialogs = document.querySelectorAll('.tox-dialog');
                dialogs.forEach(function(dialog) {
                  // Check if this dialog contains table properties
                  const labels = dialog.querySelectorAll('.tox-label');
                  labels.forEach(function(label) {
                    const labelText = label.textContent.toLowerCase();
                    
                    if (labelText.includes('width') && !label.querySelector('.unit-hint')) {
                      const unitHint = document.createElement('span');
                      unitHint.className = 'unit-hint';
                      unitHint.style.cssText = 'font-size: inherit; color: #8b949e; font-weight: normal; margin-left: 0.5rem;';
                      unitHint.textContent = '(in %)';
                      label.appendChild(unitHint);
                    }
                    
                    if (labelText.includes('height') && !label.querySelector('.unit-hint')) {
                      const unitHint = document.createElement('span');
                      unitHint.className = 'unit-hint';
                      unitHint.style.cssText = 'font-size: inherit; color: #8b949e; font-weight: normal; margin-left: 0.5rem;';
                      unitHint.textContent = '(in %)';
                      label.appendChild(unitHint);
                    }
                  });
                });
              }
            });
          });
          
          // Start observing
          observer.observe(document.body, {
            childList: true,
            subtree: true
          });
          
          // TinyMCE setup complete
        },
      });
      return true;
    };

    // If TinyMCE is not yet available, poll briefly until the CDN loads
    if (!initTiny()) {
      const start = Date.now();
      const timer = setInterval(() => {
        if (initTiny() || Date.now() - start > 5000) {
          clearInterval(timer);
        }
      }, 100);
    }
  }

  // Two-Factor Authentication Modal Functions
  window.showDisable2FA = function() {
    const modal = document.getElementById('disable-2fa-modal');
    if (modal) {
      modal.style.display = 'block';
    }
  };

  window.hideDisable2FA = function() {
    const modal = document.getElementById('disable-2fa-modal');
    if (modal) {
      modal.style.display = 'none';
    }
  };

  // Close modal when clicking outside
  window.addEventListener('click', function(event) {
    const modal = document.getElementById('disable-2fa-modal');
    if (modal && event.target === modal) {
      modal.style.display = 'none';
    }
  });

  // Two-Factor Setup Page Functions
  const showManualKeyLink = document.getElementById('show-manual-key');
  if (showManualKeyLink) {
    showManualKeyLink.addEventListener('click', function(e) {
      e.preventDefault();
      const manualSection = document.getElementById('manual-key-section');
      if (manualSection.style.display === 'none') {
        manualSection.style.display = 'block';
        this.textContent = 'Hide manual key';
      } else {
        manualSection.style.display = 'none';
        this.textContent = 'Enter the key manually';
      }
    });
  }

  // Copy to clipboard function (global)
  window.copyToClipboard = function(elementId) {
    const element = document.getElementById(elementId);
    const text = element.textContent;
    
    navigator.clipboard.writeText(text).then(function() {
      // Show success feedback
      const button = element.nextElementSibling;
      const originalText = button.innerHTML;
      button.innerHTML = '<i class="fas fa-check"></i> Copied!';
      button.classList.add('success');
      
      setTimeout(function() {
        button.innerHTML = originalText;
        button.classList.remove('success');
      }, 2000);
    }).catch(function(err) {
      console.error('Could not copy text: ', err);
    });
  };

  // Auto-format verification code input (for both setup and verify pages)
  const tokenInput = document.getElementById('token');
  if (tokenInput) {
    tokenInput.addEventListener('input', function(e) {
      // Remove non-numeric characters
      this.value = this.value.replace(/[^0-9]/g, '');
      
      // Limit to 6 digits
      if (this.value.length > 6) {
        this.value = this.value.slice(0, 6);
      }
      
      // Auto-submit when 6 digits are entered
      if (this.value.length === 6) {
        setTimeout(() => {
          this.form.submit();
        }, 500);
      }
    });
  }

  // Backup Tokens Page Functions
  // Copy individual token
  document.querySelectorAll('.copy-token').forEach(button => {
    button.addEventListener('click', function() {
      const token = this.dataset.token;
      
      navigator.clipboard.writeText(token).then(function() {
        // Show success feedback
        const originalText = this.innerHTML;
        this.innerHTML = '<i class="fas fa-check"></i> Copied!';
        this.classList.add('success');
        
        setTimeout(() => {
          this.innerHTML = originalText;
          this.classList.remove('success');
        }, 2000);
      }.bind(this)).catch(function(err) {
        console.error('Could not copy token: ', err);
      });
    });
  });

  // Copy all tokens
  const copyAllTokensBtn = document.getElementById('copy-all-tokens');
  if (copyAllTokensBtn) {
    copyAllTokensBtn.addEventListener('click', function() {
      const tokens = Array.from(document.querySelectorAll('.token-code')).map(code => code.textContent);
      const allTokens = tokens.join('\n');
      
      navigator.clipboard.writeText(allTokens).then(function() {
        // Show success feedback
        const originalText = this.innerHTML;
        this.innerHTML = '<i class="fas fa-check"></i> All Copied!';
        this.classList.add('success');
        
        setTimeout(() => {
          this.innerHTML = originalText;
          this.classList.remove('success');
        }, 2000);
      }.bind(this)).catch(function(err) {
        console.error('Could not copy tokens: ', err);
      });
    });
  }

  // Print tokens function (global)
  window.printTokens = function() {
    window.print();
  };

  // Add success styling for copied buttons
  const style = document.createElement('style');
  style.textContent = `
    .btn.success {
      background: #3fb950 !important;
      border-color: #3fb950 !important;
      color: white !important;
    }
  `;
  document.head.appendChild(style);

  // Django Admin Two-Factor Authentication Functions
  // Auto-focus on username field in admin login (but not on signup page)
  const usernameField = document.getElementById('id_username');
  const isSignupPage = document.getElementById('signup-form');
  if (usernameField && !isSignupPage) {
    usernameField.focus();
  }

  // Auto-format token inputs (for admin 2FA verification and setup)
  const adminTokenFields = document.querySelectorAll('input[name="otp_token"], input[name="token"]');
  adminTokenFields.forEach(field => {
    field.addEventListener('input', function(e) {
      // Remove non-numeric characters
      this.value = this.value.replace(/[^0-9]/g, '');
      
      // Limit to 6 digits
      if (this.value.length > 6) {
        this.value = this.value.slice(0, 6);
      }
      
      // Auto-submit when 6 digits are entered
      if (this.value.length === 6) {
        setTimeout(() => {
          this.form.submit();
        }, 500);
      }
    });

    // Focus on the token field
    field.focus();
  });

  // ==========================
  // POST FEATURED IMAGE ERROR HANDLING
  // ==========================
  // Handle post image load errors - replace with default logo
  const featuredPostImages = document.querySelectorAll('.featured-post-img');
  featuredPostImages.forEach(img => {
    img.addEventListener('error', function() {
      // Replace the image with the default logo element
      const defaultLogo = document.createElement('div');
      defaultLogo.className = 'default-post-image';
      defaultLogo.innerHTML = '<span class="logo-text">Tech Bloggers</span>';
      
      // Replace image with default logo
      this.parentElement.replaceChild(defaultLogo, this);
    });
  });

  // ==========================
  // EVENT DELEGATION FOR DATA-ACTION ATTRIBUTES
  // ==========================
  // Replace inline onclick handlers with event delegation for better CSP compliance
  
  document.addEventListener('click', function(e) {
    const target = e.target.closest('[data-action]');
    if (!target) return;
    
    const action = target.dataset.action;
    
    switch(action) {
      case 'show-disable-2fa':
        e.preventDefault();
        const showModal = document.getElementById('disable-2fa-modal');
        if (showModal) {
          showModal.style.display = 'block';
        }
        break;
        
      case 'hide-disable-2fa':
        e.preventDefault();
        const hideModal = document.getElementById('disable-2fa-modal');
        if (hideModal) {
          hideModal.style.display = 'none';
        }
        break;
        
      case 'scroll-to-top':
        e.preventDefault();
        window.scrollTo({top: 0, behavior: 'smooth'});
        break;
        
      case 'print-tokens':
        e.preventDefault();
        window.print();
        break;
        
      case 'copy-to-clipboard':
        e.preventDefault();
        const targetId = target.dataset.target;
        if (targetId) {
          const element = document.getElementById(targetId);
          if (element) {
            const text = element.textContent;
            navigator.clipboard.writeText(text).then(function() {
              // Show success feedback
              const originalText = target.innerHTML;
              target.innerHTML = '<i class="fas fa-check"></i> Copied!';
              target.classList.add('copied');
              
              setTimeout(function() {
                target.innerHTML = originalText;
                target.classList.remove('copied');
              }, 2000);
            }).catch(function(err) {
              console.error('Failed to copy: ', err);
              alert('Failed to copy to clipboard');
            });
          }
        }
        break;
    }
  });
});