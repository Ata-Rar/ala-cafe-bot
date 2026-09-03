# -*- coding: utf-8 -*-
BOT_NAME = "Ala Cafe Çalışanı"
DEFAULT_PREFIX = "!"

# Renkler
COLOR_CAFE = 0xE67E22      # Kafe Turuncusu
COLOR_SUCCESS = 0x2ECC71   # Başarı / Yeşil
COLOR_ERROR = 0xE74C3C     # Hata / Kırmızı
COLOR_INFO = 0x3498DB      # Bilgi / Mavi
COLOR_GOLD = 0xF1C40F      # Altın / VIP
COLOR_NARGILE = 0x9B59B6   # Duman Moru / Nargile

# Meşhur Nargileler & Tütün Reçeteleri
NARGILELER = {
    "imza": {
        "kategori": "🌟 Ala Özel İmza Karışımları",
        "aciklama": "Ala Cafe'nin meşhur, patentli ve en çok tercih edilen özel duman kombinasyonları.",
        "cesitler": {
            "ala_special": {
                "ad": "Ala Special (Kral Karışım)",
                "karisim": "Love 66 (%40) + Lady Killer (%30) + Mango (%20) + Hafif Buz (%10)",
                "tat_profili": "Meyvemsi, tatlı, serinletici ve yoğun beyaz duman.",
                "lule_tipi": "Phunnel Lüle (HMD / Lotus ile)",
                "koz_ayari": "3 adet 26mm hindistan cevizi közü (ilk 5 dk kapaklı, sonra kapaksız)",
                "tuyo": "Tütünleri birbirine ezmeden hafif havalandırarak harmanlayın, folyoya/metale değdirmeyin."
            },
            "bosphorus_night": {
                "ad": "Bosphorus Night (Boğaz Esintisi)",
                "karisim": "Yaban Mersini (%50) + Guava (%30) + Taze Nane (%20)",
                "tat_profili": "Mayhoş orman meyveleri ve derin ferahlatıcı duman.",
                "lule_tipi": "Glaze Phunnel veya Toprak Lüle",
                "koz_ayari": "2-3 köz dengeli dağıtılmış",
                "tuyo": "Gece seanslarında demli çay veya sodalı limonata ile muazzam eşleşir."
            },
            "havana_sunset": {
                "ad": "Havana Sunset (Tropik Günbatımı)",
                "karisim": "Ananas (%40) + Maracuja (%35) + Çarkıfelek (%25)",
                "tat_profili": "Yoğun tropikal ekşi-tatlı, asla boğaz yakmayan ferah kıvam.",
                "lule_tipi": "Phunnel Lüle",
                "koz_ayari": "3 köz",
                "tuyo": "Nargile şişesine birkaç dilim limon ve bol buz atılması lezzeti 2 katına çıkarır."
            }
        }
    },
    "klasik": {
        "kategori": "🍎 Geleneksel & Esnaf Klasikleri",
        "aciklama": "Ağır abilerin, nargile tiryakilerinin vazgeçilmez köklü tatları.",
        "cesitler": {
            "cift_elma": {
                "ad": "Nostalji Hakiki Çift Elma & Nane",
                "karisim": "Nakhla / Al Fakher Çift Elma (%80) + Nane Sakız (%20)",
                "tat_profili": "Tok anason vuruşu, yoğun duman ve klasik boğaz hissiyatı.",
                "lule_tipi": "Geleneksel Delikli Toprak Lüle (Hakiki Deri Marpuç)",
                "koz_ayari": "Doğal meşe közü veya 3 adet 26mm küp köz",
                "tuyo": "Lüleyi sıkıştırmayın, hava kanallarını açık bırakın. Yanında demlik Rize çayı şarttır!"
            },
            "uzum_nane": {
                "ad": "Efsane Siyah Üzüm & Nane",
                "karisim": "Siyah Üzüm (%70) + Nane (%30)",
                "tat_profili": "Koyu tatlı üzüm rayihası ve net nane ferahlığı.",
                "lule_tipi": "Klasik Toprak Lüle",
                "koz_ayari": "2-3 köz",
                "tuyo": "Közleri 20 dakikada bir kenarlara çevirerek tütünün yanmasını önleyin."
            }
        }
    },
    "tatli": {
        "kategori": "🍰 Tatlı & Kremsi Karışımlar",
        "aciklama": "Kahvenin yanında tatlı gibi giden gurme tütün harmanları.",
        "cesitler": {
            "pismis_seftali": {
                "ad": "Pişmiş Şeftali & Bisküvi Şöleni",
                "karisim": "Pişmiş Şeftali (%50) + Bisküvi (%30) + Vanilya (%20)",
                "tat_profili": "Fırından yeni çıkmış sıcak şeftalili tart lezzeti, yoğun tatlı duman.",
                "lule_tipi": "Phunnel Lüle (Glaze kaplamalı)",
                "koz_ayari": "2 köz (Düşük ısıda yavaş pişirme)",
                "tuyo": "Düşük ısıda uzun seans içildiğinde aroması katlanır, acele köz atmayın."
            },
            "karamel_macchiato": {
                "ad": "Karamel Sütlü Kahve",
                "karisim": "Kavrulmuş Kahve (%40) + Karamel (%40) + Süt (%20)",
                "tat_profili": "Kafede içilen latte kıvamında yumuşak ve kremsi içim.",
                "lule_tipi": "Phunnel Lüle",
                "koz_ayari": "2 köz",
                "tuyo": "Özellikle Türk kahvesiyle eşleştirildiğinde tadı damağınızda kalır."
            }
        }
    }
}
