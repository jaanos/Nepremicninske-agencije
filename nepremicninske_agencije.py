#!/usr/bin/python
# -*- encoding: utf-8 -*-

# uvozimo bottle.py
from bottleext import *

# uvozimo ustrezne podatke za povezavo
import auth_public as auth

# uvozimo psycopg2
import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE) # se znebimo problemov s šumniki

import os
import hashlib

# privzete nastavitve
SERVER_PORT = os.environ.get('BOTTLE_PORT', 8080)
RELOADER = os.environ.get('BOTTLE_RELOADER', True)
DB_PORT = os.environ.get('POSTGRES_PORT', 5432)

# Zakomentiraj, če ne želiš sporočil o napakah
debug = True

skrivnost = "rODX3ulHw3ZYRdbIVcp1IfJTDn8iQTH6TFaNBgrSkjIulr"

def nastaviSporocilo(sporocilo = None):
    # global napakaSporocilo
    staro = request.get_cookie("sporocilo", secret=skrivnost)
#    if sporocilo is None:
#        bottle.Response.delete_cookie(key='sporocilo', path='/', secret=skrivnost)
#    else:
#        bottle.Response.set_cookie(key='sporocilo', value=sporocilo, path="/", secret=skrivnost)
    return staro 

# Funkcije za izgradnjo strani

# Statične datoteke damo v mapo 'static' in do njih pridemo na naslovu '/static/...'
# Uporabno za slike in CSS, poskusi http://localhost:8080/static/slika.jpg
@get('/static/<filename:path>')
def static(filename):
    return static_file(filename, root='static')

def preveriUporabnika(): 
    uporabnisko_ime = request.get_cookie("uporabnisko_ime", secret=skrivnost)
    if uporabnisko_ime:
       # cur = baza.cursor()    
        uporabnik = None
        try: 
            cur.execute("SELECT * FROM oseba WHERE uporabnisko_ime = %s", [uporabnisko_ime])
            uporabnik = cur.fetchone()
        except:
            uporabnik = None
        if uporabnik: 
            return uporabnik
    redirect('/prijava')

####################################################################
#začetna stran
@get('/')
def hello():
    return template('prijava.html')

####################################################################
# prijava, registracija, odjava
def hashGesla(s):
    m = hashlib.sha256()
    m.update(s.encode("utf-8"))
    return m.hexdigest()

@get('/registracija')
def registracija_get():
    napaka = nastaviSporocilo()
    return template('registracija.html', napaka=napaka)

@post('/registracija')
def registracija_post():
    id = request.forms.id
    ime = request.forms.ime
    priimek = request.forms.priimek
    ulica = request.forms.ulica
    hisna_stevilka = request.forms.hisna_stevilka
    email = request.forms.email
    telefon = request.forms.telefon
    posta_id = request.forms.posta_id
    uporabnisko_ime = request.forms.uporabnisko_ime
    geslo = request.forms.geslo
    geslo2 = request.forms.geslo2
    if uporabnisko_ime is None or geslo is None or geslo2 is None:
        nastaviSporocilo('Registracija ni možna') 
        redirect('/registracija')
        return
    oseba = cur 
    uporabnik = None
    try: 
        uporabnik = cur.execute("SELECT * FROM oseba WHERE uporabnisko_ime = ?", [uporabnisko_ime])
    except:
        uporabnik = None
    if uporabnik is None:
        nastaviSporocilo('Registracija ni možna') 
        redirect('/registracija')
        return
    if len(geslo) < 4:
        nastaviSporocilo('Geslo mora imeti vsaj 4 znake.') 
        redirect('/registracija')
        return
    if geslo != geslo2:
        nastaviSporocilo('Gesli se ne ujemata.') 
        redirect('/registracija')
        return
    zgostitev = hashGesla(geslo)
    cur.execute("""INSERT INTO oseba
                (id,ime,priimek,ulica, hisna_stevilka, email,telefon, posta_id, uporabnisko_ime, geslo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", (id,ime,priimek,ulica, hisna_stevilka, email,telefon, posta_id, uporabnisko_ime, zgostitev))
    response.set_cookie(key='uporabnisko_ime', value=uporabnisko_ime, path='/', secret=skrivnost)
    redirect('/osebe')


@get('/prijava')
def prijava_get():
    return template('prijava.html')

@post('/prijava')
def prijava_post():
    uporabnisko_ime = request.forms.uporabnisko_ime
    geslo = request.forms.geslo
    if uporabnisko_ime is None or geslo is None:
        nastaviSporocilo('Uporabniško ima in geslo morata biti neprazna') 
        redirect('/prijava')
        return
    oseba = cur   
    hashBaza = None
    try: 
        hashBaza = cur.execute("SELECT geslo FROM oseba WHERE uporabnisko_ime = %s", (uporabnisko_ime, ))
        hashBaza = cur.fetchone()
        hashBaza = hashBaza[0]
    except:
        hashBaza = None
    if hashBaza is None:
        nastaviSporocilo('Uporabniško geslo ali ime nista ustrezni') 
        redirect('/prijava')
        return
    if hashGesla(geslo) == hashBaza or geslo == hashBaza:
        response.set_cookie('uporabnisko_ime', uporabnisko_ime, secret=skrivnost)
        
        redirect('/index')
        return
    else:
        nastaviSporocilo('Uporabniško geslo ali ime nista ustrezni') 
        redirect('/prijava')
        return

@get('/index')
def index():
    uporabnik = request.get_cookie('uporabnisko_ime', secret=skrivnost)
    emso = cur.execute("""SELECT emso from oseba where uporabnisko_ime = %s""", uporabnik)
    if emso in cur.execute("""SELECT id FROM agent"""):
        return template('oseba.html')
    else:
        return template('index.html')

    
@get('/odjava')
def odjava_get():
    bottle.Response.delete_cookie(key='uporabnisko_ime')
    redirect('/prijava')

####################################################################
@get('/oseba')
def oseba():
    cur.execute("""
    SELECT id, ime, priimek, ulica, hisna_stevilka, email, telefon, posta.postna_stevilka , posta.posta, uporabnisko_ime, geslo FROM oseba
    INNER JOIN posta ON posta.postna_stevilka = oseba.posta_id
    ORDER BY oseba.priimek """)
    return template('oseba.html', oseba=cur)

@get('/dodaj_oseba')
def dodaj_oseba():
    return template('dodaj_oseba.html', id='', ime='', priimek='', ulica='', hisna_stevilka='', email='', telefon='', posta_id='', uporabnisko_ime='', geslo='', napaka=None)

@post('/dodaj_oseba')
def dodaj_oseba_post():
    id = request.forms.id
    ime = request.forms.ime
    priimek = request.forms.priimek
    ulica = request.forms.ulica
    hisna_stevilka = request.forms.hisna_stevilka
    email = request.forms.email
    telefon = request.forms.telefon
    posta_id = request.forms.posta_id
    uporabnisko_ime = request.forms.uporabnisko_ime
    geslo = request.forms.geslo
    
    try:
        cur.execute("INSERT INTO oseba (id, ime, priimek, ulica, hisna_stevilka, email, telefon, posta_id, uporabnisko_ime, geslo) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (id, ime, priimek, ulica, hisna_stevilka, email, telefon, posta_id, uporabnisko_ime, geslo))
        conn.commit()
    except Exception as ex:
        conn.rollback()
        return template('dodaj_oseba.html', id=id, ime=ime, priimek=priimek, ulica=ulica, hisna_stevilka=hisna_stevilka, email=email, telefon=telefon, posta_id=posta_id, uporabnisko_ime=uporabnisko_ime, geslo=geslo,
                        napaka='Zgodila se je napaka: %s' % ex)
    redirect(url('/oseba'))

def najdi_id_osebe():
    cur.execute("SELECT id, ime, priimek, ulica, hisna_stevilka, email, telefon, posta_id, uporabnisko_ime, geslo FROM oseba;")
    return cur.fetchall()

@get('/uredi_oseba')
def uredi_oseba():
    #uporabnik = preveriUporabnika()
    #if uporabnik is None: 
        #return
    return template('uredi_oseba.html', id='', ime='', priimek='', ulica='', hisna_stevilka='', email='', telefon='', posta_id='', uporabnisko_ime='', geslo='', napaka=None, oseba=najdi_id_osebe())

@post('/uredi_oseba')
def uredi_oseba_post():
    #uporabnik = preveriUporabnika()
    #if uporabnik is None: 
        #return
    id = request.forms.id
    ime = request.forms.ime
    try:
        cur.execute("UPDATE oseba SET ime=%s WHERE id=%s",
                    (id, ime, priimek, ulica, hisna_stevilka, email, telefon, posta_id, Uporabnisko_ime, geslo))
        conn.commit()
    except Exception as ex:
        conn.rollback()
        return template('uredi_oseba.html', id=id, ime=ime, priimek=priimek, ulica=ulica, hisna_stevilka=hisna_stevilka, email=email, telefon=telefon, posta_id=posta_id, uporabnisko_ime=uporabnisko_ime, geslo=geslo,
                        napaka='Zgodila se je napaka: %s' % ex)
    redirect(url('oseba'))

@get('/komitent')
def komitent():
    cur.execute("""
    SELECT id_komitent, oseba.ime, oseba.priimek, kupuje_nepremicnino, njegov_agent FROM komitent
    LEFT JOIN oseba ON komitent.id_komitent = oseba.id
     """)
    return template('komitent.html', komitent=cur)

#tabela agenta
@get('/agent')
def agent():
    cur.execute("""
    SELECT id_agent, oseba.ime, oseba.priimek, plača, agencija, agencija.ime FROM agent
    LEFT JOIN oseba ON agent.id_agent = oseba.id
    LEFT JOIN agencija ON agent.agencija = agencija.id
     """)
    return template('agent.html', agent=cur)

@get('/posta')
def posta():
    cur.execute("""
        SELECT * FROM posta
    """)
    return template('posta.html', posta=cur)

@get('/nepremicnina')
def nepremicnina():
    cur.execute("""
        SELECT nepremicnina.id, velikost, cena, ulica, hisna_stevilka, postna_stevilka, leto_izgradnje, kupuje_agencija FROM nepremicnina
        INNER JOIN agencija ON agencija.id = nepremicnina.kupuje_agencija
    """)
    return template('nepremicnina.html', nepremicnina=cur)

######################################################################
# Glavni program
# tu bi se priklopili na bazo

# Poženemo strežnik na portu 8080, glej http://localhost:8080/
# Iz bottle dokumentacije o parametru reloader=True: Every time you edit a module file, 
# the reloader restarts the server process and loads the newest version of your code. 
conn = psycopg2.connect(database='sem2022_ninav', host='baza.fmf.uni-lj.si', user='javnost', password='javnogeslo')
conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) # onemogocimo transakcije
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) 
run(host='localhost', port=8080, reloader=True)

######################################################################