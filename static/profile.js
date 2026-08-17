// profile.js - Profile image upload, preview, crop, and save logic
// Requires Cropper.js

let cropper = null;

window.loadProfileImage = async function() {
    // Fetch current profile image from backend and set preview
    const imgTag = document.getElementById('profileImgTag');
    const placeholder = document.getElementById('profileImgPlaceholder');
    try {
        const res = await fetch('/api/profile/image-url');
        const data = await res.json();
        if (data.url) {
            imgTag.src = data.url + '?t=' + Date.now();
            imgTag.style.display = 'block';
            placeholder.style.display = 'none';
            // Also update navbar avatar if exists
            const userLogo = document.querySelector('.user-logo img');
            if(userLogo) userLogo.src = data.url + '?t=' + Date.now();
        } else {
            imgTag.style.display = 'none';
            placeholder.style.display = 'block';
            // Remove navbar avatar image if exists
            const userLogo = document.querySelector('.user-logo img');
            if(userLogo) userLogo.remove();
        }
    } catch {
        imgTag.style.display = 'none';
        placeholder.style.display = 'block';
    }
};

const imgInput = document.getElementById('profileImgInput');
const cropContainer = document.getElementById('profileCropContainer');
const saveBtn = document.getElementById('saveProfileImgBtn');

if(imgInput) {
    imgInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = function(evt) {
            cropContainer.innerHTML = `<img id='cropperImg' src='${evt.target.result}' style='max-width:100%;max-height:180px;' />`;
            cropContainer.style.display = 'block';
            saveBtn.style.display = 'inline-block';
            if (cropper) cropper.destroy();
            const cropperImg = document.getElementById('cropperImg');
            cropper = new Cropper(cropperImg, {
                aspectRatio: 1,
                viewMode: 1,
                dragMode: 'move',
                autoCropArea: 1,
                minContainerWidth: 180,
                minContainerHeight: 180,
                background: false,
                movable: true,
                zoomable: true,
                rotatable: false,
                scalable: false
            });
        };
        reader.readAsDataURL(file);
    });
}

if(saveBtn) {
    saveBtn.addEventListener('click', async function() {
        if (!cropper) return;
        const canvas = cropper.getCroppedCanvas({ width: 220, height: 220, imageSmoothingQuality: 'high' });
        canvas.toBlob(async function(blob) {
            // Upload to backend
            const formData = new FormData();
            formData.append('profile_image', blob, 'profile.png');
            saveBtn.textContent = 'Saving...';
            saveBtn.disabled = true;
            try {
                const res = await fetch('/api/profile/upload-image', {
                    method: 'POST',
                    body: formData
                });
                if (res.ok) {
                    // Update preview
                    const url = URL.createObjectURL(blob);
                    document.getElementById('profileImgTag').src = url;
                    document.getElementById('profileImgTag').style.display = 'block';
                    document.getElementById('profileImgPlaceholder').style.display = 'none';
                    cropContainer.style.display = 'none';
                    saveBtn.style.display = 'none';
                    imgInput.value = '';
                    // Update navbar avatar if exists
                    const userLogo = document.querySelector('.user-logo img');
                    if(userLogo) userLogo.src = url;
                    else {
                        // If .user-logo is a div, add img
                        const logoDiv = document.querySelector('.user-logo');
                        if(logoDiv && !logoDiv.querySelector('img')) {
                            logoDiv.innerHTML = `<img src='${url}' style='width:100%;height:100%;object-fit:cover;border-radius:50%;' alt='Profile' />`;
                        }
                    }
                    alert('Profile image updated!');
                } else {
                    alert('Failed to upload image.');
                }
            } catch (err) {
                alert('Error uploading image.');
            }
            saveBtn.textContent = 'Save';
            saveBtn.disabled = false;
    }, 'image/png', 0.95);
    });
}
