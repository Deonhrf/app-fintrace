from flask import Flask, render_template, request,redirect, url_for, session
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

@app.route('/logout')
def logout():
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)