import csv
import os
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any


# MODEL SINIFLARI
class Movie:
    """Tek bir filmi temsil eder."""
    def __init__(self, movie_id: int, title: str, times: List[str]) -> None:
        self._id = movie_id
        self._title = title
        self._times = list(times)
   
    """Neden private kullanıldı film bilgileri sistem tarafından kontrol edilmelidir ve
kullanıcının veya başka bir sınıfın film ID’sini veya seans listesini doğrudan değiştirmesi engellenmiştir."""

    @property
    def id(self) -> int:
        return self._id

    @property
    def title(self) -> str:
        return self._title

    @property
    def times(self) -> List[str]:
        return list(self._times)
    
    """Neden property kullanıldı dış dünyaya kontrollü ve güvenli erişim sağlamak için """

class Ticket:
    """Satılan bileti temsil eder (CSV'ye yazılan kayıt)."""
    def __init__(self, timestamp: str, movie: str, time: str, seat: str,
                 ticket_type: str, price: float, buyer: str) -> None:
        self._timestamp = timestamp
        self._movie = movie
        self._time = time
        self._seat = seat
        self._ticket_type = ticket_type
        self._price = price
        self._buyer = buyer
    
    """Tüm alanların privete olmasının sebebi bilet oluşturulduktan sonra değiştirmemelidir."""

    def to_csv_row(self) -> List[Any]:
        return [
            self._timestamp,
            self._movie,
            self._time,
            self._seat,
            self._ticket_type,
            self._price,
            self._buyer
        ]

"""to_csv_row metodunun kullanılma sebebi ticket dosyasına yazılabilmesi için gerekli format dönüşümünü yapar """

# DEPO (STORE) + KALITIM 
class BaseStore:
    
    """Dosya tabanlı depolar için ortak üst sınıf (kalıtım göstermek için).
    Neden kalıtım kullanıldı JSON VE CSV dosyaları farklı formatlar olsa da ortak olarak bir dosya yoluna ihtiyaç duyar
    Kod tekrarını önlemek için BasesStore soyut bir temel gibi kullanılmıştır """
    
    def __init__(self, path: str) -> None:
        self._path = path

    @property
    def path(self) -> str:
        return self._path


class JsonSeatStore(BaseStore):
    """Koltuk durumunu JSON dosyasında saklar.Kalıtım kullanılmış"""
    def __init__(self, path: str) -> None:
        super().__init__(path)

    def exists(self) -> bool:
        return os.path.exists(self._path)

    def load(self) -> Dict[str, Dict[str, bool]]:
        with open(self._path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, seats: Dict[str, Dict[str, bool]]) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(seats, f, ensure_ascii=False, indent=2)


class CsvTicketStore(BaseStore):
    """Bilet kayıtlarını CSV dosyasına ekler.Kalıtım kullanılmış"""
    def __init__(self, path: str) -> None:
        super().__init__(path)

    def append_ticket(self, ticket: Ticket) -> None:
        exists = os.path.exists(self._path)
        with open(self._path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not exists:
                writer.writerow([
                    "timestamp", "movie", "time",
                    "seat", "ticket_type", "price", "buyer"
                ])
            writer.writerow(ticket.to_csv_row())


# SERVIS SINIFLARI
class CatalogService:
    """Film kataloğunu yönetir."""
    def __init__(self, movies: Dict[int, Dict[str, Any]]) -> None:
        self._movies: Dict[int, Movie] = {
            mid: Movie(mid, m["title"], m["times"])
            for mid, m in movies.items()
        }
    
    """Private kullanılmasının sebebi sadece servis tarafından yönetilir """
    
    def list_movies(self) -> List[Movie]:
        return [self._movies[mid] for mid in sorted(self._movies.keys())]

    def get_movie(self, movie_id: int) -> Movie:
        return self._movies[movie_id]

    def has_movie(self, movie_id: int) -> bool:
        return movie_id in self._movies


class PricingService:
    
    """Bilet türleri ve fiyatlarını yönetir."""
    
    def __init__(self, prices: Dict[str, float]) -> None:
        self._prices = dict(prices)

    def types(self) -> List[str]:
        return list(self._prices.keys())

    def price_of(self, ticket_type: str) -> float:
        return float(self._prices[ticket_type])


class SeatService:
    """Koltuk planını üretir, yükler, günceller.""" 
    def __init__(self, store: JsonSeatStore, rows: Tuple[str, ...], cols: int, catalog: CatalogService) -> None:
        self._store = store
        self._rows = rows
        self._cols = cols
        self._catalog = catalog

    def _make_empty_seats(self) -> Dict[str, bool]:
        return {f"{r}{c}": True for r in self._rows for c in range(1, self._cols + 1)}

    def load_or_init(self) -> Dict[str, Dict[str, bool]]:
        if self._store.exists():
            return self._store.load()

        seats: Dict[str, Dict[str, bool]] = {}
        for movie in self._catalog.list_movies():
            for t in movie.times:
                seats[f"{movie.id}_{t}"] = self._make_empty_seats()

        self._store.save(seats)
        return seats

    def save(self, seats: Dict[str, Dict[str, bool]]) -> None:
        self._store.save(seats)


# UI (TERMINAL) SINIFI
class ConsoleUI:
    """Konsol etkileşimlerini tek yerde toplar."""
    def clear_console(self) -> None:
        os.system("cls" if os.name == "nt" else "clear")

    def get_valid_name(self) -> str:
        while True:
            name = input("Ad Soyad: ").strip()

            if not name:
                print("❌ İsim boş bırakılamaz.")
                continue

            if any(char.isdigit() for char in name):
                print("❌ İsim sayı içeremez.")
                continue

            if not all(char.isalpha() or char.isspace() for char in name):
                print("❌ İsim sadece harf ve boşluk içermelidir.")
                continue

            return name

    def print_movies(self, movies: List[Movie]) -> None:
        print("Mevcut Filmler:\n")
        for m in movies:
            print(f"{m.id}. {m.title}  |  Seanslar: {', '.join(m.times)}")
        print()

    def choose_movie(self, catalog: CatalogService) -> int:
        while True:
            try:
                choice = int(input("Film numarası: "))
                if catalog.has_movie(choice):
                    return choice
                print("❌ Geçersiz film.")
            except ValueError:
                print("❌ Lütfen sayı girin.")

    def choose_time(self, movie: Movie) -> str:
        times = movie.times
        while True:
            t = input("Seans saati: ").strip()
            if t in times:
                return t
            print("❌ Geçersiz seans.")

    def print_seats(self, seat_map: Dict[str, bool], rows: Tuple[str, ...], cols: int) -> None:
        print("\nKoltuk Planı (O=Boş, X=Dolu)")
        print("   " + " ".join(f"{i:>2}" for i in range(1, cols + 1)))
        for r in rows:
            row_line = f"{r} "
            for c in range(1, cols + 1):
                row_line += "  O" if seat_map[f"{r}{c}"] else "  X"
            print(row_line)
        print()

    def choose_seat(self, seat_map: Dict[str, bool], rows: Tuple[str, ...], cols: int) -> str:
        while True:
            self.print_seats(seat_map, rows, cols)
            seat = input("Koltuk (A1 gibi): ").upper().strip()
            if seat in seat_map:
                if seat_map[seat]:
                    return seat
                print("❌ Bu koltuk dolu.")
            else:
                print("❌ Geçersiz koltuk.")

    def choose_ticket_type(self, pricing: PricingService) -> str:
        types = pricing.types()
        print("\nBilet Türleri:")
        for i, t in enumerate(types, 1):
            print(f"{i}. {t} - {pricing.price_of(t)} TL")

        while True:
            try:
                choice = int(input("Bilet türü numarası: "))
                if 1 <= choice <= len(types):
                    return types[choice - 1]
                print("❌ Geçersiz seçim.")
            except ValueError:
                print("❌ Lütfen sayı girin.")


# UYGULAMA
class TicketSaleApp:
    """Tüm akışı yöneten ana sınıf."""
    def __init__(self,
                 ui: ConsoleUI,
                 catalog: CatalogService,
                 pricing: PricingService,
                 seat_service: SeatService,
                 ticket_store: CsvTicketStore,
                 rows: Tuple[str, ...],
                 cols: int) -> None:
        self._ui = ui
        self._catalog = catalog
        self._pricing = pricing
        self._seat_service = seat_service
        self._ticket_store = ticket_store
        self._rows = rows
        self._cols = cols
       
        """private veri bütünlüğğünü ve kapsülleme iççin kullanılmış 
        public metotlar güvenli ve kontrollü erişimi sağladığı içn kullanılmış"""
        
        # Koltuk verisini uygulama başında yükle/oluştur
        self._seats = self._seat_service.load_or_init()

    def run_once(self) -> None:
        self._ui.clear_console()
        print("=== SİNEMA BİLET SATIŞ SİSTEMİ ===\n")

        buyer = self._ui.get_valid_name()
        self._ui.print_movies(self._catalog.list_movies())

        movie_id = self._ui.choose_movie(self._catalog)
        movie = self._catalog.get_movie(movie_id)
        time = self._ui.choose_time(movie)

        session_key = f"{movie_id}_{time}"
        seat_map = self._seats[session_key]

        seat = self._ui.choose_seat(seat_map, self._rows, self._cols)
        ticket_type = self._ui.choose_ticket_type(self._pricing)
        price = self._pricing.price_of(ticket_type)

        self._ui.clear_console()
        print("=== SATIŞ ÖZETİ ===\n")
        print(f"Kullanıcı Adı : {buyer}")
        print(f"Film          : {movie.title}")
        print(f"Seans         : {time}")
        print(f"Koltuk        : {seat}")
        print(f"Bilet Türü    : {ticket_type}")
        print(f"Ücret         : {price} TL")

        confirm = input("\nSatın almayı onaylıyor musunuz? (E/h): ").lower()
        if confirm != "e":
            print("\n❌ Satın alma iptal edildi.")
            return

        # koltuk doldur + json kaydet
        seat_map[seat] = False
        self._seat_service.save(self._seats)

        # bilet oluştur + csv kaydet
        ticket = Ticket(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            movie=movie.title,
            time=time,
            seat=seat,
            ticket_type=ticket_type,
            price=price,
            buyer=buyer
        )
        self._ticket_store.append_ticket(ticket)

        print("\n✅ Satın alma başarılı!")
        print("Biletiniz kaydedildi.\n")

    def run_forever(self) -> None:
        while True:
            self.run_once()
            again = input("Yeni satış yapmak ister misiniz? (E/h): ").lower()
            if again != "e":
                print("\nBilet başarı ile satın alındı. İyi günler!")
                break


# SABİT VERİLER
MOVIES = {
    1: {"title": "Gölgeler Şehri", "times": ["14:00", "17:00", "20:00"]},
    2: {"title": "Yıldızlara Yolculuk", "times": ["13:30", "16:30", "19:30"]},
    3: {"title": "Komedi Gecesi", "times": ["15:00", "18:00", "21:00"]}
}

PRICES = {
    "Yetişkin": 60.0,
    "Öğrenci": 40.0,
    "Çocuk": 30.0
}

ROWS = ("A", "B", "C", "D", "E")
COLS = 8

TICKETS_CSV = "tickets.csv"
SEATS_JSON = "seats.json"

# ÇALIŞTIRMA
if __name__ == "__main__":
    ui = ConsoleUI()
    catalog = CatalogService(MOVIES)
    pricing = PricingService(PRICES)

    seat_store = JsonSeatStore(SEATS_JSON)
    ticket_store = CsvTicketStore(TICKETS_CSV)

    seat_service = SeatService(seat_store, ROWS, COLS, catalog)

    app = TicketSaleApp(
        ui=ui,
        catalog=catalog,
        pricing=pricing,
        seat_service=seat_service,
        ticket_store=ticket_store,
        rows=ROWS,
        cols=COLS
    )
    app.run_forever()