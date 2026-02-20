from flask import Flask, render_template, request, redirect, url_for
import pulp
import json
import os

app = Flask(__name__)

# Veritabanı Dosyası
DB_FILE = 'oyuncular.json'
oyuncular_db = []
id_counter = 0

# --- VERİTABANI İŞLEMLERİ (KAYDET & YÜKLE) ---
def verileri_yukle():
    """Uygulama açılırken dosyadan verileri okur."""
    global oyuncular_db, id_counter
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                oyuncular_db = json.load(f)
            
            # ID sayacını en son kalınan yerden devam ettir
            if oyuncular_db:
                max_id = max(o['id'] for o in oyuncular_db)
                id_counter = max_id + 1
            else:
                id_counter = 0
        except:
            oyuncular_db = []
            id_counter = 0
    else:
        oyuncular_db = []
        id_counter = 0

def verileri_kaydet():
    """Herhangi bir değişiklikte verileri dosyaya yazar."""
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(oyuncular_db, f, ensure_ascii=False, indent=4)

# Uygulama başlarken verileri yükle
verileri_yukle()

# --- PUAN HESAPLAMA MOTORU ---
def hesapla_fm_puani(mevki_kodu, attr):
    skor = 0
    if mevki_kodu == "GK":
        skor = (attr['refleks']*0.30 + attr['birebir']*0.20 + attr['elle_kontrol']*0.15 + attr['pozisyon']*0.15 + attr['konsantrasyon']*0.10 + attr['pas']*0.10)
    elif mevki_kodu == "CB": 
        skor = (attr['markaj']*0.25 + attr['top_calma']*0.25 + attr['kafa']*0.20 + attr['guc']*0.15 + attr['pozisyon']*0.10 + attr['kararlilik']*0.05)
    elif mevki_kodu in ["LB", "RB", "LWB", "RWB"]: 
        skor = (attr['hiz']*0.20 + attr['top_calma']*0.20 + attr['orta_yapma']*0.15 + attr['dayaniklilik']*0.15 + attr['markaj']*0.10 + attr['pozisyon']*0.10 + attr['pas']*0.10)
    elif mevki_kodu == "CDM":
        skor = (attr['top_calma']*0.20 + attr['guc']*0.15 + attr['pas']*0.15 + attr['pozisyon']*0.15 + attr['dayaniklilik']*0.15 + attr['karar']*0.10 + attr['markaj']*0.10)
    elif mevki_kodu == "CM":
        skor = (attr['pas']*0.25 + attr['vizyon']*0.20 + attr['dayaniklilik']*0.15 + attr['teknik']*0.10 + attr['top_calma']*0.10 + attr['karar']*0.10 + attr['ilk_dokunus']*0.10)
    elif mevki_kodu == "CAM":
        skor = (attr['vizyon']*0.25 + attr['pas']*0.20 + attr['teknik']*0.20 + attr['top_surme']*0.15 + attr['uzaktan_sut']*0.10 + attr['karar']*0.10)
    elif mevki_kodu in ["LW", "RW", "LM", "RM"]:
        skor = (attr['hiz']*0.25 + attr['top_surme']*0.20 + attr['orta_yapma']*0.15 + attr['teknik']*0.15 + attr['hizlanma']*0.15 + attr['bitiricilik']*0.10)
    elif mevki_kodu in ["ST", "CF"]:
        skor = (attr['bitiricilik']*0.30 + attr['top_suz_alan']*0.20 + attr['kafa']*0.15 + attr['sogukkanlilik']*0.15 + attr['hiz']*0.10 + attr['guc']*0.10)
    return round(skor, 1)

def get_kritik_ozellikler(mevki):
    if mevki == "GK": return ["refleks", "birebir", "elle_kontrol"]
    elif mevki == "CB": return ["markaj", "top_calma", "kafa"]
    elif mevki in ["LB", "RB", "LWB", "RWB"]: return ["hiz", "top_calma", "orta_yapma"]
    elif mevki == "CDM": return ["top_calma", "guc", "pas"]
    elif mevki in ["CM", "CAM"]: return ["pas", "vizyon", "teknik"]
    elif mevki in ["LM", "RM", "LW", "RW"]: return ["hiz", "top_surme", "orta_yapma"]
    elif mevki in ["ST", "CF"]: return ["bitiricilik", "top_suz_alan", "sogukkanlilik"]
    return ["pas", "guc", "hiz"]

# --- ROTALAR ---

@app.route('/')
def index():
    return render_template('index.html', oyuncular=oyuncular_db, sonuc=None)

@app.route('/ekle', methods=['POST'])
def ekle():
    global id_counter
    isim = request.form.get('isim')
    mevki_1 = request.form.get('mevki_1')
    mevki_2 = request.form.get('mevki_2')
    if mevki_2 == "Yok": mevki_2 = None
    liderlik = int(request.form.get('liderlik', 50))

    attributes = {k: int(v) for k, v in request.form.items() if k not in ['isim', 'mevki_1', 'mevki_2', 'liderlik']}
    
    defaults = {'bitiricilik':50, 'pas':50, 'hiz':50, 'guc':50, 'markaj':50, 'top_calma':50, 'refleks':10, 'birebir':10, 'elle_kontrol':10, 'pozisyon':50, 'vizyon':50, 'karar':50, 'orta_yapma':50, 'teknik':50, 'sogukkanlilik':50, 'top_suz_alan':50, 'kafa':50, 'kararlilik':50, 'caliskanlik':50, 'hizlanma':50, 'dayaniklilik':50, 'ziplama':50, 'denge':50, 'ilk_dokunus':50, 'top_surme':50, 'uzaktan_sut':50, 'agresiflik':50, 'konsantrasyon':50}
    for k, v in defaults.items():
        if k not in attributes: attributes[k] = v

    puan_1 = hesapla_fm_puani(mevki_1, attributes)
    puan_2 = 0
    if mevki_2: puan_2 = hesapla_fm_puani(mevki_2, attributes)

    oyuncular_db.append({
        "id": id_counter, "isim": isim, "mevkiler": [mevki_1, mevki_2] if mevki_2 else [mevki_1],
        "puanlar": {mevki_1: puan_1, mevki_2: puan_2} if mevki_2 else {mevki_1: puan_1},
        "attr": attributes, "liderlik": liderlik
    })
    id_counter += 1
    
    # KAYDET
    verileri_kaydet()
    
    return redirect(url_for('index'))

@app.route('/sil/<int:id>')
def sil(id):
    global oyuncular_db
    oyuncular_db = [o for o in oyuncular_db if o['id'] != id]
    # KAYDET
    verileri_kaydet()
    return redirect(url_for('index'))

@app.route('/sifirla')
def sifirla():
    global oyuncular_db, id_counter
    oyuncular_db = []
    id_counter = 0
    # KAYDET (Boş haliyle)
    verileri_kaydet()
    return redirect(url_for('index'))

@app.route('/ornek_veri')
def ornek_veri():
    global id_counter, oyuncular_db
    oyuncular_db = []
    id_counter = 0

    # GS KADROSU 
    gs_kadro = [
        {"isim": "F. Muslera", "mevkiler": ["GK"], "liderlik": 95, "attr": {'refleks':95, 'birebir':90, 'elle_kontrol':88, 'pozisyon':90, 'pas':65, 'konsantrasyon':90, 'hiz':40, 'guc':75, 'bitiricilik':5, 'markaj':5, 'top_calma':5, 'orta_yapma':5, 'kafa':5, 'teknik':50, 'agresiflik':60, 'vizyon':50, 'karar':80, 'sogukkanlilik':85, 'top_suz_alan':10, 'kararlilik':85, 'caliskanlik':70, 'hizlanma':40, 'dayaniklilik':60, 'ziplama':70, 'denge':60, 'ilk_dokunus':40, 'top_surme':20, 'uzaktan_sut':5}},
        {"isim": "Davinson Sanchez", "mevkiler": ["CB"], "liderlik": 75, "attr": {'markaj':88, 'top_calma':90, 'kafa':88, 'guc':92, 'hiz':88, 'pozisyon':82, 'pas':75, 'kararlilik':85, 'bitiricilik':40, 'orta_yapma':30, 'teknik':70, 'refleks':5, 'birebir':5, 'elle_kontrol':5, 'agresiflik':92, 'vizyon':60, 'karar':75, 'sogukkanlilik':75, 'konsantrasyon':80, 'top_suz_alan':30, 'caliskanlik':85, 'hizlanma':85, 'dayaniklilik':85, 'ziplama':88, 'denge':80, 'ilk_dokunus':70, 'top_surme':60, 'uzaktan_sut':40}},
        {"isim": "Ismail Jakobs", "mevkiler": ["LB", "LWB"], "liderlik": 60, "attr": {'hiz':92, 'hizlanma':90, 'orta_yapma':75, 'top_calma':78, 'markaj':75, 'dayaniklilik':88, 'guc':75, 'pas':70, 'bitiricilik':50, 'kafa':65, 'teknik':72, 'refleks':5, 'birebir':5, 'elle_kontrol':5, 'agresiflik':75, 'pozisyon':70, 'vizyon':60, 'karar':70, 'sogukkanlilik':70, 'konsantrasyon':75, 'top_suz_alan':70, 'kararlilik':80, 'caliskanlik':85, 'ziplama':70, 'denge':75, 'ilk_dokunus':70, 'top_surme':78, 'uzaktan_sut':55}},
        {"isim": "Kaan Ayhan", "mevkiler": ["CB", "RB", "CDM"], "liderlik": 75, "attr": {'markaj':82, 'top_calma':85, 'pas':85, 'vizyon':75, 'pozisyon':85, 'guc':80, 'hiz':65, 'teknik':78, 'bitiricilik':50, 'orta_yapma':65, 'kafa':75, 'refleks':5, 'birebir':5, 'elle_kontrol':5, 'agresiflik':70, 'karar':80, 'sogukkanlilik':80, 'konsantrasyon':80, 'top_suz_alan':50, 'kararlilik':75, 'caliskanlik':75, 'hizlanma':60, 'dayaniklilik':75, 'ziplama':70, 'denge':75, 'ilk_dokunus':75, 'top_surme':60, 'uzaktan_sut':60}},
        {"isim": "Lucas Torreira", "mevkiler": ["CDM", "CM"], "liderlik": 82, "attr": {'top_calma':95, 'markaj':90, 'agresiflik':95, 'dayaniklilik':99, 'pas':85, 'pozisyon':92, 'kararlilik':95, 'caliskanlik':99, 'hiz':75, 'guc':70, 'bitiricilik':55, 'orta_yapma':50, 'kafa':55, 'teknik':82, 'refleks':5, 'birebir':5, 'elle_kontrol':5, 'vizyon':80, 'karar':85, 'sogukkanlilik':85, 'konsantrasyon':95, 'top_suz_alan':70, 'hizlanma':80, 'ziplama':50, 'denge':92, 'ilk_dokunus':80, 'top_surme':70, 'uzaktan_sut':60}},
        {"isim": "Gabriel Sara", "mevkiler": ["CM", "CAM"], "liderlik": 65, "attr": {'pas':92, 'vizyon':94, 'teknik':90, 'uzaktan_sut':88, 'orta_yapma':88, 'top_surme':82, 'dayaniklilik':85, 'hiz':75, 'bitiricilik':78, 'markaj':55, 'top_calma':65, 'kafa':60, 'refleks':5, 'birebir':5, 'elle_kontrol':5, 'agresiflik':65, 'pozisyon':75, 'karar':80, 'sogukkanlilik':82, 'konsantrasyon':80, 'top_suz_alan':82, 'kararlilik':80, 'caliskanlik':85, 'hizlanma':78, 'ziplama':65, 'denge':80, 'ilk_dokunus':85, 'guc':75}},
        {"isim": "Barış Alper Yılmaz", "mevkiler": ["RW", "LW", "ST", "RB", "LB"], "liderlik": 70, "attr": {'hiz':99, 'hizlanma':97, 'guc':95, 'dayaniklilik':95, 'caliskanlik':98, 'top_surme':88, 'agresiflik':95, 'bitiricilik':75, 'orta_yapma':75, 'pas':72, 'markaj':60, 'top_calma':65, 'kafa':82, 'teknik':76, 'refleks':5, 'birebir':5, 'elle_kontrol':5, 'pozisyon':75, 'vizyon':65, 'karar':72, 'sogukkanlilik':72, 'konsantrasyon':78, 'top_suz_alan':85, 'kararlilik':98, 'ziplama':92, 'denge':88, 'ilk_dokunus':75, 'uzaktan_sut':70}},
        {"isim": "Victor Osimhen", "mevkiler": ["ST"], "liderlik": 80, "attr": {'bitiricilik':94, 'kafa':98, 'hiz':96, 'guc':95, 'top_suz_alan':92, 'ziplama':99, 'agresiflik':90, 'kararlilik':95, 'sogukkanlilik':85, 'pas':65, 'teknik':80, 'markaj':30, 'top_calma':35, 'orta_yapma':50, 'refleks':5, 'birebir':5, 'elle_kontrol':5, 'pozisyon':85, 'vizyon':60, 'karar':75, 'konsantrasyon':85, 'caliskanlik':95, 'hizlanma':92, 'dayaniklilik':90, 'denge':85, 'ilk_dokunus':80, 'top_surme':75, 'uzaktan_sut':70}},
        {"isim": "Yunus Akgün", "mevkiler": ["RW", "LW", "CAM"], "liderlik": 55, "attr": {'top_surme':88, 'hizlanma':88, 'teknik':86, 'pas':78, 'vizyon':78, 'bitiricilik':75, 'uzaktan_sut':80, 'hiz':85, 'orta_yapma':78, 'dayaniklilik':72, 'guc':60, 'markaj':35, 'top_calma':40, 'kafa':45, 'refleks':5, 'birebir':5, 'elle_kontrol':5, 'agresiflik':60, 'pozisyon':72, 'karar':72, 'sogukkanlilik':74, 'konsantrasyon':72, 'top_suz_alan':78, 'kararlilik':75, 'caliskanlik':80, 'ziplama':50, 'denge':80, 'ilk_dokunus':85}},
        {"isim": "Mauro Icardi", "mevkiler": ["ST"], "liderlik": 92, "attr": {'bitiricilik': 98, 'top_suz_alan': 99, 'sogukkanlilik': 99, 'kafa': 88, 'pozisyon': 95, 'karar': 90, 'ilk_dokunus': 88, 'teknik': 85, 'pas': 78, 'vizyon': 80, 'guc': 80, 'hiz': 60, 'markaj': 20, 'top_calma': 30, 'orta_yapma': 60, 'refleks': 5, 'birebir': 5, 'elle_kontrol': 5, 'agresiflik': 60, 'konsantrasyon': 90, 'kararlilik': 80, 'caliskanlik': 60, 'hizlanma': 60, 'dayaniklilik': 65, 'ziplama': 75, 'denge': 80, 'top_surme': 70, 'uzaktan_sut': 75}},
        {"isim": "Eren Elmalı", "mevkiler": ["LB"], "liderlik": 55, "attr": {'hiz':80, 'hizlanma':82, 'orta_yapma':72, 'top_calma':75, 'markaj':72, 'dayaniklilik':85, 'guc':70, 'pas':68, 'bitiricilik':45, 'kafa':60, 'teknik':68, 'refleks':5, 'birebir':5, 'elle_kontrol':5, 'agresiflik':80, 'pozisyon':70, 'vizyon':55, 'karar':65, 'sogukkanlilik':65, 'konsantrasyon':70, 'top_suz_alan':65, 'kararlilik':85, 'caliskanlik':90, 'ziplama':65, 'denge':70, 'ilk_dokunus':68, 'top_surme':70, 'uzaktan_sut':50}},
        {"isim": "Dries Mertens", "mevkiler": ["CAM", "CF"], "liderlik": 85, "attr": {'vizyon':90, 'pas':88, 'teknik':92, 'uzaktan_sut':85, 'bitiricilik':85, 'orta_yapma':85, 'top_surme':82, 'ilk_dokunus':90, 'karar':90, 'sogukkanlilik':90, 'top_suz_alan':92, 'hiz':65, 'hizlanma':70, 'guc':50, 'dayaniklilik':60, 'markaj':30, 'top_calma':40, 'kafa':50, 'refleks':5, 'birebir':5, 'elle_kontrol':5, 'agresiflik':65, 'pozisyon':80, 'konsantrasyon':85, 'kararlilik':85, 'caliskanlik':80, 'ziplama':40, 'denge':85}},
        {"isim": "Gunay Guvenc", "mevkiler": ["GK"], "liderlik": 65, "attr": {'refleks':82, 'birebir':80, 'elle_kontrol':80, 'pozisyon':80, 'pas':65, 'konsantrasyon':75, 'hiz':40, 'guc':70, 'bitiricilik':5, 'markaj':5, 'top_calma':5, 'orta_yapma':5, 'kafa':10, 'teknik':55, 'agresiflik':60, 'vizyon':50, 'karar':70, 'sogukkanlilik':75, 'top_suz_alan':5, 'kararlilik':75, 'caliskanlik':70, 'hizlanma':40, 'dayaniklilik':60, 'ziplama':70, 'denge':60, 'ilk_dokunus':40, 'top_surme':15, 'uzaktan_sut':5}},
        {"isim": "Roland Sallai", "mevkiler": ["RW", "LW"], "liderlik": 65, "attr": {'hiz':82, 'hizlanma':84, 'top_surme':80, 'orta_yapma':80, 'bitiricilik':78, 'pas':76, 'teknik':82, 'ilk_dokunus':82, 'guc':72, 'dayaniklilik':85, 'markaj':45, 'top_calma':50, 'kafa':65, 'refleks':5, 'birebir':5, 'elle_kontrol':5, 'agresiflik':75, 'pozisyon':78, 'vizyon':75, 'karar':75, 'sogukkanlilik':75, 'konsantrasyon':78, 'top_suz_alan':82, 'kararlilik':85, 'caliskanlik':90, 'ziplama':65, 'denge':75, 'uzaktan_sut':70}},
        {"isim": "Abdülkerim Bardakcı", "mevkiler": ["CB", "LB"], "liderlik": 65,  "attr": {'markaj': 70,         'top_calma': 70,      'kafa': 78,          'pas': 72,            'teknik': 65,'ilk_dokunus': 60,'top_surme': 60,'orta_yapma': 55,'bitiricilik': 40,'uzaktan_sut': 50,     'agresiflik': 85,'kararlilik': 75,     'pozisyon': 70,'konsantrasyon': 75,'sogukkanlilik': 75,'karar': 70,'vizyon': 65,'caliskanlik': 75,'top_suz_alan': 50,'guc': 78,'denge': 75,'ziplama': 70,'dayaniklilik': 65,'hiz': 55,'hizlanma': 50,'refleks': 10, 'birebir': 10, 'elle_kontrol': 10}}
    ]
    
    for o in gs_kadro:
        puanlar = {}
        for m in o["mevkiler"]:
            puanlar[m] = hesapla_fm_puani(m, o["attr"])
        oyuncular_db.append({"id": id_counter, "isim": o["isim"], "mevkiler": o["mevkiler"], "puanlar": puanlar, "attr": o["attr"], "liderlik": o["liderlik"]})
        id_counter += 1
    
    # KAYDET
    verileri_kaydet()
    
    return redirect(url_for('index'))

@app.route('/optimize', methods=['POST'])
def optimize():
    try: hedef_kisi = int(request.form.get('kisi_sayisi', 11))
    except: hedef_kisi = 11
    dizilis = request.form.get('dizilis', 'farketmez')

    model = pulp.LpProblem("Detayli_Kadro_V2", pulp.LpMaximize)
    
    olasi_atamalar = []
    for o in oyuncular_db:
        for m in o["mevkiler"]: olasi_atamalar.append((o["id"], m))

    x = pulp.LpVariable.dicts("Oyna", olasi_atamalar, 0, 1, pulp.LpBinary)
    k = pulp.LpVariable.dicts("Kaptan", [o["id"] for o in oyuncular_db], 0, 1, pulp.LpBinary)

    model += pulp.lpSum([oyuncular_db[i]["puanlar"][m] * x[(i, m)] for i, m in olasi_atamalar]) + \
             pulp.lpSum([oyuncular_db[i]["liderlik"] * k[i] for i in range(len(oyuncular_db))])

    model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar]) == hedef_kisi
    model += pulp.lpSum([k[i] for i in range(len(oyuncular_db))]) == 1
    
    for i in range(len(oyuncular_db)):
        model += pulp.lpSum([x[(i, m)] for m in oyuncular_db[i]["mevkiler"]]) <= 1
        model += k[i] <= pulp.lpSum([x[(i, m)] for m in oyuncular_db[i]["mevkiler"]])

    model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar if m == "GK"]) == 1
    model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar if m == "LB"]) <= 1
    model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar if m == "RB"]) <= 1
    model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar if m == "LWB"]) <= 1
    model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar if m == "RWB"]) <= 1
    
    if dizilis != "farketmez":
        try:
            parts = dizilis.split('-') 
            def_sayisi = int(parts[0])
            mid_sayisi = int(parts[1])
            fw_sayisi = int(parts[2])

            if def_sayisi == 4:
                model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar if m == "LB"]) == 1
                model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar if m == "RB"]) == 1
                model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar if m == "CB"]) == 2
            elif def_sayisi == 3:
                model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar if m == "CB"]) == 3
                model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar if m in ["LB", "RB"]]) == 0
            elif def_sayisi == 5:
                model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar if m == "LB"]) == 1
                model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar if m == "RB"]) == 1
                model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar if m == "CB"]) == 3
            else:
                 model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar if m in ["LB", "RB", "CB", "LWB", "RWB"]]) == def_sayisi
            
            if fw_sayisi == 3:
                model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar if m == "LW"]) == 1
                model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar if m == "RW"]) == 1
                model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar if m in ["ST", "CF"]]) == 1
            elif fw_sayisi == 1:
                model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar if m in ["ST", "CF"]]) == 1
            
            def_set = ["CB", "LB", "RB", "LWB", "RWB"]
            mid_set = ["CDM", "CM", "CAM", "LM", "RM"]
            fw_set = ["ST", "CF", "LW", "RW"]
            
            if fw_sayisi != 3:
                model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar if m in mid_set]) == mid_sayisi
                model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar if m in fw_set]) == fw_sayisi

        except:
             return render_template('index.html', oyuncular=oyuncular_db, hata="Diziliş formatı desteklenmiyor!")
    
    else:
        model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar if m == "LB"]) <= 1
        model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar if m == "RB"]) <= 1
        model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar if m == "CB"]) >= 1
        model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar if m in ["CDM", "CM", "CAM"]]) >= 1
        model += pulp.lpSum([x[(i, m)] for i, m in olasi_atamalar if m in ["ST", "CF"]]) >= 1

    model.solve()

    if pulp.LpStatus[model.status] != 'Optimal':
         return render_template('index.html', oyuncular=oyuncular_db, hata="Çözüm bulunamadı! Seçilen diziliş için uygun mevkide oyuncu yok.")

    secilen_kadro = []
    toplam_guc = 0
    kaptan_isim = ""
    siralama = {"GK":1, "CB":2, "LB":3, "RB":4, "LWB":5, "RWB":6, "CDM":7, "CM":8, "LM":9, "RM":10, "CAM":11, "LW":12, "RW":13, "ST":14, "CF":15}

    for i, m in olasi_atamalar:
        if x[(i, m)].value() == 1:
            o = oyuncular_db[i].copy()
            o["oynanan_mevki"] = m
            o["oynanan_puan"] = o["puanlar"][m]
            o["rol"] = "KAPTAN ⭐" if k[i].value() == 1 else "Oyuncu"
            if k[i].value() == 1: kaptan_isim = o["isim"]
            
            kritik_keys = get_kritik_ozellikler(m)
            o["sebeb_stats"] = {k: o["attr"][k] for k in kritik_keys}
            
            secilen_kadro.append(o)
            toplam_guc += o["oynanan_puan"]

    secilen_kadro.sort(key=lambda k: siralama.get(k["oynanan_mevki"], 99))

    return render_template('index.html', oyuncular=oyuncular_db, sonuc=secilen_kadro, guc=round(toplam_guc,1), kaptan=kaptan_isim, tercih=dizilis)

if __name__ == '__main__':
    app.run(debug=True)