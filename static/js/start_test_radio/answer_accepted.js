const btn = document.getElementById('answer_btn');
btn.addEventListener('click', () => {
      btn.style.display = 'none';
      const box = document.getElementById('wait');
      box.style.display = 'block';
    });