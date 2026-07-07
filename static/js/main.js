// Toggle Password untuk Semua Halaman (Login, Register, Profile)
document.addEventListener('DOMContentLoaded', function() {
    
    const toggleButtons = document.querySelectorAll('.toggle-password');

    toggleButtons.forEach(button => {
        button.addEventListener('click', function () {
            const input = this.previousElementSibling;   // Ambil input password di sebelah kiri tombol
            
            if (input) {
                if (input.type === 'password') {
                    input.type = 'text';
                    this.textContent = '🙈';
                } else {
                    input.type = 'password';
                    this.textContent = '👁️';
                }
            }
        });
    });
});


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
