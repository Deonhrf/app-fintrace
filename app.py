from flask import Flask, render_template, request,redirect, url_for, session, Response, flash
import pymysql
import json
import math

app = Flask(__name__)
app.secret_key = 'fintrace_rahasia_super_aman_123'
# connect to the database
mydb = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    database='db_pencatatan_keuangan'
)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    id_user = session['user_id']

    if request.method == 'POST':
        tx_type = request.form.get('type') # pemasukan atau pengeluaran
        amount = request.form.get('amount')
        category = request.form.get('category')
        description = request.form.get('description')
        date = request.form.get('date')
        
        # SOLUSI: Masukkan id_user ke dalam antrean data INSERT
        value = (id_user, tx_type, amount, category, description, date)
        query = "INSERT INTO transactions (user_id, type, amount, category, description, date) VALUES (%s, %s, %s, %s, %s, %s)"
        
        mycur = mydb.cursor()
        mycur.execute(query, value)
        mydb.commit()
        mycur.close()

        return redirect(url_for('dashboard'))
    
    # Mode membaca data (GET)
    mycur = mydb.cursor(pymysql.cursors.DictCursor)

    # SOLUSI: Kunci total pengeluaran hanya untuk ID user yang sedang login
    mycur.execute("SELECT SUM(amount) as total FROM transactions WHERE user_id=%s AND type='pengeluaran'", (id_user,))
    result = mycur.fetchone()
    total_keluar = result['total'] if result and result['total'] else 0

    # SOLUSI: Kunci total pemasukan hanya untuk ID user yang sedang login
    mycur.execute("SELECT SUM(amount) as total FROM transactions WHERE user_id=%s AND type='pemasukan'", (id_user,))
    result = mycur.fetchone()
    total_masuk = result['total'] if result and result['total'] else 0

    # Hitung Saldo privat
    total_saldo = total_masuk - total_keluar

    # Query Riwayat Transaksi 
    mycur.execute("""
        SELECT 
            DATE_FORMAT(date, '%%d %%b %%Y') as date, 
            description, 
            category, 
            type, 
            amount 
        FROM transactions 
        WHERE user_id = %s 
        ORDER BY transactions.date DESC, id DESC 
        LIMIT 5
    """, (id_user,))
    riwayat_transaksi = mycur.fetchall()

    # Query Grafik
    mycur.execute("""
        SELECT category, SUM(amount) as total_nominal 
        FROM transactions 
        WHERE user_id = %s AND type = 'pengeluaran' 
        GROUP BY category
    """, (id_user,))
    data_chart = mycur.fetchall()
    mycur.close()

    chart_labels = [item['category'].capitalize() for item in data_chart]
    chart_values = [float(item['total_nominal']) for item in data_chart]

    # SOLUSI UTAMA: Mengubah nama parameter menjadi 'riwayat=' agar klop dengan HTML
    return render_template('dashboard.html',
                            saldo=total_saldo,
                            pemasukan=total_masuk,
                            pengeluaran=total_keluar,
                            riwayat=riwayat_transaksi, # <-- Diubah dari riwayat_transaksi menjadi riwayat
                            chart_labels=json.dumps(chart_labels), # Di-serialize agar aman dibaca JS
                            chart_values=json.dumps(chart_values)  # Di-serialize agar aman dibaca JS
                            )
@app.route('/login', methods=['GET', 'POST'])
def login():
    query = "select id, username, password, email from users where username=%s and password=%s"
    if request.method == 'POST':
        user = request.form['username']
        password = request.form['password']
        value = (user, password)
        mycur = mydb.cursor()
        mycur.execute(query, value)
        result = mycur.fetchone()
        mycur.close()
        if result and password == result[2]:
            session['user_id'] = result[0]
            session['name'] = result[1]
            session['email'] = result[3] 
            return redirect('/dashboard')
        else: 
            return render_template('login.html', error="Nama atau Password Salah")
    else:
        return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    query = "insert into users (username,email, password) values (%s, %s, %s)"
    if request.method == 'POST':
      username = request.form['username']
      email = request.form['email']
      password = request.form['password']
      value = (username, email, password)
      mycur = mydb.cursor()
      mycur.execute(query, value)
      mydb.commit()
      mycur.close()
      return redirect('/login')
    else : 
        return render_template('register.html')
    

@app.route('/transaksi', methods=['GET', 'POST'])
def transaksi():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    id_user = session['user_id']
    pesan_teks = None

    if request.method == 'POST':
        type = request.form.get('jenis') # Pemasukkan atau pengeluaran
        amount = request.form.get('nominal')
        category = request.form.get('kategori')
        description = request.form.get('keterangan')
        date = request.form.get('tanggal')
        
        # Simpan dalam database
        value = (id_user, type, amount, category, description, date)
        query = "insert into transactions (user_id, type, amount, category, description, date) values (%s, %s, %s, %s, %s, %s)"
        mycur = mydb.cursor()
        mycur.execute(query, value)
        mydb.commit()
        mycur.close()

        pesan_teks = "Transaksi berhasil dicatat!"

    mycur = mydb.cursor(pymysql.cursors.DictCursor)
    mycur.execute("""
        SELECT 
            description, 
            category, 
            type, 
            amount 
        FROM transactions 
        WHERE user_id = %s 
        ORDER BY id DESC 
        LIMIT 2
    """, (id_user,))
    data_mini = mycur.fetchall()
    mycur.close()

    return render_template('transaksi.html',
                           pesan = pesan_teks,
                           transaksi_terakhir = data_mini)


@app.route('/riwayat', methods=['GET'])
def riwayat():
    # 1. BENTENG KEAMANAN: Pastikan user wajib login terlebih dahulu
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    id_user = session['user_id']

    # 2. KONFIGURASI HALAMAN (PAGINASI)
    try:
        page = int(request.args.get('page', 1))
        if page < 1: page = 1
    except ValueError:
        page = 1

    per_page = 10
    offset = (page - 1) * per_page

    # 3. TANGKAP INPUT FILTER DARI URL (GET REQUEST)
    search_query = request.args.get('search', '')
    filter_category = request.args.get('category', '')
    filter_type = request.args.get('type', '')

    # Menggunakan DictCursor agar data kembalian MySQL berbentuk Dictionary (klop dengan HTML)
    mycur = mydb.cursor(pymysql.cursors.DictCursor)

    # 4. TAHAP HITUNG TOTAL DATA (Mengikuti Filter yang Sedang Aktif)
    count_query = "SELECT COUNT(*) as total FROM transactions WHERE user_id = %s"
    count_params = [id_user]

    if search_query:
        count_query += " AND description LIKE %s"
        count_params.append(f"%{search_query}%")
    if filter_category:
        count_query += " AND category = %s"
        count_params.append(filter_category)
    if filter_type:
        count_query += " AND type = %s"
        count_params.append(filter_type)

    # Eksekusi penghitungan total baris data terlebih dahulu
    mycur.execute(count_query, tuple(count_params))
    total_data = mycur.fetchone()['total'] # <-- Variabel total_data RESMI tercipta di sini

    # Hitung batas maksimal halaman secara matematis (Urutan logis setelah total_data lahir)
    total_pages = math.ceil(total_data / per_page)
    if total_pages == 0: total_pages = 1

    # 5. TAHAP AMBIL DATA TRANSAKSI UTAMA (Dibatasi berdasarkan LIMIT & OFFSET)
    query = """
        SELECT 
            id,
            DATE_FORMAT(date, '%%d %%b %%Y') as date, 
            description, 
            category, 
            type, 
            amount 
        FROM transactions 
        WHERE user_id = %s
    """
    params = [id_user]

    if search_query:
        query += " AND description LIKE %s"
        params.append(f"%{search_query}%")
    if filter_category:
        query += " AND category = %s"
        params.append(filter_category)
    if filter_type:
        query += " AND type = %s"
        params.append(filter_type)

    # Tambahkan pengurutan kronologis data terbaru dan batasan paginasi
    query += " ORDER BY transactions.date DESC, id DESC LIMIT %s OFFSET %s"
    params.extend([per_page, offset])

    # Eksekusi pengambilan data utama
    mycur.execute(query, tuple(params))
    seluruh_riwayat = mycur.fetchall()
    mycur.close()

    # 6. HITUNG METADATA TAMPILAN UNTUK FOOTER TABEL HTML
    start_num = (page - 1) * per_page + 1 if seluruh_riwayat else 0
    end_num = min(page * per_page, total_data)

    # 7. LEMPAR VARIABEL SECARA UTUH KE HTML
    return render_template('riwayat.html', 
                           riwayat=seluruh_riwayat,
                           search=search_query,
                           selected_category=filter_category,
                           selected_type=filter_type,
                           current_page=page,
                           total_pages=total_pages,
                           total_data=total_data,
                           start_num=start_num,
                           end_num=end_num)
@app.route('/ekspor', methods=['GET'])
def ekspor_laporan():
    # 1. Benteng Keamanan: Wajib login
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    id_user = session['user_id']
    mycur = mydb.cursor(pymysql.cursors.DictCursor)
    
    # 2. Ambil seluruh data transaksi privat tanpa LIMIT
    mycur.execute("""
        SELECT 
            DATE_FORMAT(date, '%%d-%%m-%%Y') as tanggal, 
            description, 
            category, 
            type, 
            amount 
        FROM transactions 
        WHERE user_id = %s 
        ORDER BY date DESC, id DESC
    """, (id_user,))
    data_transaksi = mycur.fetchall()
    mycur.close()

    # 3. Logika Generator CSV: Menulis baris demi baris ke dalam memori buffer
    def generate():
        # Buat Header Kolom Laporan
        header = ['Tanggal', 'Keterangan', 'Kategori', 'Jenis Transaksi', 'Nominal (Rp)']
        yield ','.join(header) + '\n'
        
        # Iterasi masukkan data database ke baris di bawah header
        for row in data_transaksi:
            baris = [
                row['tanggal'],
                f'"{row["description"]}"', # Dibungkus kutip ganda aman dari spasi/koma teks
                row['category'].capitalize(),
                row['type'].capitalize(),
                str(int(row['amount'])) # Ubah decimal ke teks angka bulat
            ]
            yield ','.join(baris) + '\n'

    # 4. Return Object Response dengan Header khusus agar Browser mendownload berkas
    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=Laporan_FinTrace_Mei_2026.csv"}
    )



# Aksi-hapus
@app.route('/hapus/<int:id_tx>', methods=['POST'])
def hapus_transaksi(id_tx):
    # Session
    if 'user_id' not in session:
        return redirect(url_for('login'))
    id_user = session['user_id']

    mycur = mydb.cursor(pymysql.cursors.DictCursor)

    query = 'Delete from transactions where id = %s and user_id = %s'
    mycur.execute(query, (id_tx, id_user))
    mydb.commit()
    mycur.close()

    flash('Transaksi berhasil dihapus', 'success')
    return redirect(url_for('riwayat'))


# Aksi-edit
@app.route('/edit-transaksi/<int:id_tx>', methods=['GET', 'POST'])
def edit_transaksi(id_tx):
    # Keamanan: Pastikan user wajib login terlebih dahulu
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    id_user = session['user_id']
    mycur = mydb.cursor(pymysql.cursors.DictCursor)

    # Ambil data transaksi yang akan diedit, pastikan transaksi tersebut milik user yang sedang login
    if request.method == 'POST':
        type = request.form.get('jenis')
        amount = request.form.get('nominal')
        category = request.form.get('kategori')
        description = request.form.get('keterangan')
        date = request.form.get('tanggal')

        query = "update transactions set type=%s, amount=%s, category=%s, description=%s, date=%s where id=%s and user_id=%s"
        mycur.execute(query, (type, amount, category, description, date, id_tx, id_user))
        mydb.commit()
        mycur.close()

        flash('Transaksi berhasil diperbarui', 'success')
        return redirect(url_for('riwayat'))
    

    # Mode GET: Ambil data lama untuk dilempar ke form edit
    mycur.execute("SELECT * FROM transactions WHERE id = %s AND user_id = %s", (id_tx, id_user))
    data_lama = mycur.fetchone()
    mycur.close()
    
    if not data_lama:
        flash("Data tidak ditemukan!", "danger")
        return redirect(url_for('riwayat'))
        
    # Pinjam halaman templates/transaksi.html untuk mengedit data
    return render_template('transaksi.html', data_edit=data_lama)
    
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('profile.html')

@app.route('/update_profile', methods=['POST'])
def update_profile() :
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    id_user = session['user_id']
    nama_baru = request.form.get('name')
    email_baru = request.form.get('email')

    mycur = mydb.cursor()
    query = "update users set username=%s, email=%s where id=%s"
    mycur.execute(query, (nama_baru, email_baru, id_user))
    mydb.commit()
    mycur.close()

    # update session agar nama yang tampil di navbar juga berubah
    session['name'] = nama_baru
    flash('Profil berhasil diperbarui', 'success')
    return redirect(url_for('profile'))

@app.route('/update_password', methods=['POST'])
def update_password():
    if 'user_id' not in session:
        return redirect(url_for(login))
    
    id_user = session('user_id')
    sandi_lama = request.form.get('old_password')
    sandi_baru = request.form.get('new_password')
    confirm_sandi_baru = request.form.get('confirm_password')

    # Logika - Pencocokan apakaha sandi baru sesuai dengan konfirmasi yang diinputkan
    if sandi_baru != confirm_sandi_baru:
        flash('Konfirmasi sandi baru tidak cocok!', 'danger')
        return redirect(url_for('profile'))
    
    # Logika - Cek apakah sandi lama benar
    mycur = mydb.cursor()
    mycur.execute("SELECT password FROM users WHERE id = %s", (id_user,))
    user_data = mycur.fetchone()

    # Logika Cek 2: Apakah sandi lama sesuai dengan data di database?
    mycur = mydb.cursor()
    mycur.execute("SELECT password FROM users WHERE id = %s", (id_user,))
    user_data = mycur.fetchone()
    
    # Di sini kita asumsikan teks biasa, nanti di industri nyata wajib di-hash
    if user_data and sandi_lama == user_data[0]:
        # Jika benar, eksekusi pembaruan
        mycur.execute("UPDATE users SET password = %s WHERE id = %s", (sandi_baru, id_user))
        mydb.commit()
        mycur.close()
        flash("Kata sandi berhasil diperbarui!", "success")
    else:
        mycur.close()
        flash("Kata sandi saat ini yang Anda masukkan salah!", "danger")
        
    return redirect(url_for('pengaturan'))

# hapus_akun
app.route('/hapus_akun', methods=['POST'])
def hapus_akun():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    id_user = session['user_id']
    # 2. Eksekusi Penghapusan di Database Pusat (MySQL)
    mycur = mydb.cursor()
    # Menghapus user murni dari tabel users. 
    # Karena foreign key diatur 'ON DELETE CASCADE', tabel transactions akan dibersihkan otomatis oleh MySQL.
    query = "DELETE FROM users WHERE id = %s"
    mycur.execute(query, (id_user,))
    mydb.commit()
    mycur.close()
    
    # 3. Hancurkan Kunci Kartu Akses (Session RAM) sampai bersih plong
    session.clear()
    
    # 4. Beri pesan perpisahan di halaman login
    flash("Akun Anda telah dihapus permanen dari sistem FinTrace. Terima kasih!", "success")
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)