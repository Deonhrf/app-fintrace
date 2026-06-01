from flask import Flask, render_template, request,redirect, url_for, session, Response
import pymysql
import json


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
    query = "select id, username, password from users where username=%s and password=%s"
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

        return redirect(url_for('dashboard'))
    
    return render_template('transaksi.html')


@app.route('/riwayat', methods=['GET'])
def riwayat():
    # 1. BENTENG KEAMANAN: Pastikan user wajib login terlebih dahulu
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    id_user = session['user_id']
    
    # 2. TANGKAP INPUT FILTER: Mengambil parameter pencarian dari URL (GET Request)
    search_query = request.args.get('search', '')
    filter_category = request.args.get('category', '')
    filter_type = request.args.get('type', '')

    # 3. KONEKSI & AMBIL DATA: Wajib gunakan DictCursor agar klop dengan HTML (tx.date, tx.description)
    mycur = mydb.cursor(pymysql.cursors.DictCursor)

    # Base query dasar untuk mengambil semua data milik user yang aktif
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

    # LOGIKA FILTER DINAMIS (Anti-Vibe Coding):
    # Jika kolom pencarian diisi oleh user
    if search_query:
        query += " AND description LIKE %s"
        params.append(f"%{search_query}%")

    # Jika drop-down kategori dipilih
    if filter_category:
        query += " AND category = %s"
        params.append(filter_category)

    # Jika drop-down jenis transaksi dipilih (pemasukan/pengeluaran)
    if filter_type:
        query += " AND type = %s"
        params.append(filter_type)

    # Urutkan data secara kronologis dari yang paling baru dimasukkan
    query += " ORDER BY transactions.date DESC, id DESC"

    # Eksekusi query gabungan beserta parameternya yang aman dari SQL Injection
    mycur.execute(query, tuple(params))
    seluruh_riwayat = mycur.fetchall()
    mycur.close()

    # 4. LEMPAR KE HTML: Samakan nama parameternya 'riwayat=' agar terbaca oleh {% if riwayat %}
    return render_template('riwayat.html', 
                           riwayat=seluruh_riwayat,
                           search=search_query,
                           selected_category=filter_category,
                           selected_type=filter_type)


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

@app.route('/logout')
def logout():
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)