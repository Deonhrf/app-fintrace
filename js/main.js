function togglePassword() {
      const passwordInput = document.getElementById('passwordInput');
      const eyeIcon = document.getElementById('eyeIcon');
      
      if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        // Ubah isi SVG menjadi ikon "Mata Tertutup/Dicoret"
        eyeIcon.innerHTML = `
          <path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 0 0 1.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.451 10.451 0 0 1 12 4.5c4.756 0 8.773 3.162 10.065 7.498a10.522 10.522 0 0 1-4.293 5.774M6.228 6.228 3 3m3.228 3.228 3.65 3.65m7.815 7.815 3 3m-3-3-3.65-3.65m0 0a3 3 0 1 0-4.243-4.243m4.242 4.242L9.88 9.88" />
        `;
      } else {
        passwordInput.type = 'password';
        // Kembalikan isi SVG ke ikon "Mata Terbuka"
        eyeIcon.innerHTML = `
          <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0" />
        `;
      }
    }

// Transaksi
    document.addEventListener('DOMContentLoaded', function() {
        const radioJenis = document.querySelectorAll('input[name="jenis"]');
        const kategoriSelect = document.getElementById('kategori-select');
        const kategoriOptions = kategoriSelect.querySelectorAll('option');

        function filterKategori() {
            // Ambil value dari radio button yang aktif ('pengeluaran' atau 'pemasukan')
            const jenisAktif = document.querySelector('input[name="jenis"]:checked').value;
            let opsiTerpilihMasihAda = false;

            kategoriOptions.forEach(option => {
                const dataType = option.getAttribute('data-type');
                
                // Lewati opsi placeholder pertama
                if (!dataType) return;

                // Logika penyaringan dinamis
                if (dataType === jenisAktif || dataType === 'both') {
                    option.style.display = 'block';
                    option.disabled = false;
                    if (option.selected) opsiTerpilihMasihAda = true;
                } else {
                    option.style.display = 'none';
                    option.disabled = true;
                    if (option.selected) option.selected = false;
                }
            });

            // Jika opsi lama hangus karena pergantian jenis, kembalikan value select ke default placeholder
            if (!opsiTerpilihMasihAda && !kategoriOptions[0].selected) {
                kategoriSelect.value = "";
            }
        }

        // Jalankan pasang event listener untuk melacak setiap perubahan tombol radio
        radioJenis.forEach(radio => {
            radio.addEventListener('change', filterKategori);
        });

        // Eksekusi langsung sekali di awal agar sinkron saat pertama kali memuat halaman (mode edit)
        filterKategori();
    });


// profile
  // 1. Cari semua tombol mata di dalam halaman
  const toggleButtons = document.querySelectorAll('.toggle-password');

  // 2. Berikan "tugas mendengarkan klik" ke setiap tombol mata
  toggleButtons.forEach(button => {
    button.addEventListener('click', function () {
      // Cari kotak input yang berada tepat di sebelah tombol mata ini
      const input = this.previousElementSibling;
      
      // Sakelar logika: Jika tipenya password, ubah ke text. Jika text, kembalikan ke password.
      if (input.type === 'password') {
        input.type = 'text';
        this.textContent = '🙈'; // Berubah jadi monyet tutup mata saat sandi terlihat
      } else {
        input.type = 'password';
        this.textContent = '👁️'; // Kembali jadi mata terbuka saat sandi disembunyikan
      }
    });
  });