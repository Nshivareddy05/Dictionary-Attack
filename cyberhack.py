import streamlit as st
import hashlib
import itertools
import time
import string
from concurrent.futures import ThreadPoolExecutor

HASH_ALGOS = {
    "MD5": hashlib.md5,
    "SHA-256": hashlib.sha256,
    "SHA-512": hashlib.sha512
}

SPECIAL_CHARS = ["@", "#", "!", "_", "$", "%", "&", "*"]
COMMON_SUFFIXES = ["123", "007", "99", "2000", "2024", "!", "_"]
LEET_MAP = {"a": "@", "o": "0", "e": "3", "i": "1", "s": "$", "t": "7"}

def hash_password(password, algo="SHA-256"):
    return HASH_ALGOS[algo](password.encode()).hexdigest()

def generate_variations(word):
    if not word:
        return []
    
    word = word.strip()
    words = word.split()
    base_variations = set()
    
    base_variations.add(word.lower())
    base_variations.add(word.capitalize())
    base_variations.add(word.upper())
    base_variations.add("".join(words))
    base_variations.add("_".join(words))
    base_variations.add("-".join(words))
    
    for w in list(base_variations):
        for char, leet in LEET_MAP.items():
            base_variations.add(w.replace(char, leet))
            base_variations.add(w.replace(char.upper(), leet))
    
    for w in list(base_variations):
        for special in SPECIAL_CHARS:
            base_variations.add(w + special)
            base_variations.add(special + w)
    
    all_combinations = set()
    for length in range(1, len(word) + 1):
        for combo in itertools.permutations(word, length):
            all_combinations.add("".join(combo))
    
    base_variations.update(all_combinations)
    
    return list(base_variations)

def generate_password_list(details, extra_words, dob):
    base_words = details + extra_words
    all_variations = set()
    
    for word in base_words:
        all_variations.update(generate_variations(word))
    
    final_list = set(all_variations)
    dob_patterns = [
        dob.replace("-", ""), dob.replace("-", " "),
        dob[:2], dob[-2:], dob[:4],
        dob.replace("-", "").replace("0", ""),
    ]
    
    for word in all_variations:
        for pattern in dob_patterns:
            final_list.add(f"{word}{pattern}")
            final_list.add(f"{word}@{pattern}")
            final_list.add(f"{word}!{pattern}")
        for char in SPECIAL_CHARS:
            final_list.add(f"{word}{char}")
            final_list.add(f"{char}{word}")
        for suffix in COMMON_SUFFIXES:
            final_list.add(f"{word}{suffix}")
            final_list.add(f"{word}@{suffix}")
    
    with open("password_list.txt", "w") as f:
        for pwd in final_list:
            f.write(pwd + "\n")
    
    return final_list

def dictionary_attack(password, wordlist, hashed=False, algo="SHA-256"):
    start_time = time.time()
    password_hash = hash_password(password, algo) if hashed else password
    
    for word in wordlist:
        if hashed:
            if hash_password(word, algo) == password_hash:
                return word, round(time.time() - start_time, 4)
        else:
            if word == password:
                return word, round(time.time() - start_time, 4)
    
    return None, round(time.time() - start_time, 4)

def brute_force_attack(password, charset, min_len, max_len, hashed=False, algo="SHA-256"):
    start_time = time.time()
    password_hash = hash_password(password, algo) if hashed else password
    
    def attempt(pwd):
        return hash_password(pwd, algo) if hashed else pwd
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        for length in range(min_len, max_len + 1):
            for combo in itertools.product(charset, repeat=length):
                generated_password = ''.join(combo)
                if executor.submit(attempt, generated_password).result() == password_hash:
                    return generated_password, round(time.time() - start_time, 4)
    
    return None, round(time.time() - start_time, 4)

st.title("🔐Password Cracker Using Dictonary and BruteForce Attack")
st.subheader("Test passwords against dictionary & brute-force attacks.")

name = st.text_input("Your Name")
dob = st.text_input("Date of Birth (DD-MM-YYYY)")
pet = st.text_input("Pet's Name")
mother = st.text_input("Mother's Name")
sibling = st.text_input("Sibling's Name")
crush = st.text_input("Crush's Name")
phone = st.text_input("Phone Number")
imp_date = st.text_input("Important Date (DDMMYYYY)")
extra_words = st.text_input("Additional words (comma-separated)")
password = st.text_input("Enter Password to Test", type="password")

min_len = st.slider("Brute Force Min Length", 1, 8, 4)
max_len = st.slider("Brute Force Max Length", 4, 12, 9)
charset = string.ascii_letters + string.digits + string.punctuation

if st.button("🔍 Start Cracking"):
    details = [name, pet, mother, sibling, crush, phone[-4:], dob, imp_date]
    extra_words = extra_words.split(",") if extra_words else []
    dictionary = generate_password_list(details, extra_words, dob)
    st.success(f"📁 Password list saved. Total Words: {len(dictionary)}")
    
    if password:
        found, time_taken = dictionary_attack(password, dictionary)
        if found:
            st.error(f"❌ Password cracked: `{found}` in {time_taken} sec")
        else:
            st.success("✅ Password not found in dictionary. Trying brute-force...")
            found, time_taken = brute_force_attack(password, charset, min_len, max_len)
            if found:
                st.error(f"❌ Password cracked via brute-force: `{found}` in {time_taken} sec")
            else:
                st.success("✅ Password not cracked.")
