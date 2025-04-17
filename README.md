# LinkedIn Auto Applicant

[English](#english) | [Türkçe](#türkçe)

## English

### Description
LinkedIn Auto Applicant is an automated tool designed to streamline the job application process on LinkedIn. It uses web automation to scrape job details, generate personalized application content, and submit applications automatically.

### Features
- Automated job application process
- Customizable application templates
- Support for multiple job postings
- Configurable settings
- Headless mode support

### Installation
1. Clone the repository:
```bash
git clone https://github.com/kker4m/linkedin-auto-applicant.git
cd linkedin-auto-applicant
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `settings.json` file with your configuration:
```json
{
    "openai_api_key": "your-api-key-here"
}
```

### Usage
1. Configure your settings in `settings.json`
2. Run the application:
```bash
python main.py
```

## Türkçe

### Açıklama
LinkedIn Auto Applicant, LinkedIn'deki iş başvuru sürecini otomatikleştirmek için tasarlanmış bir araçtır. Web otomasyonu kullanarak iş ilanlarını tarar, kişiselleştirilmiş başvuru içeriği oluşturur ve başvuruları otomatik olarak gönderir.

### Özellikler
- Otomatik iş başvuru süreci
- Özelleştirilebilir başvuru şablonları
- Birden fazla iş ilanı desteği
- Yapılandırılabilir ayarlar
- Arka planda çalışma modu desteği

### Kurulum
1. Depoyu klonlayın:
```bash
git clone https://github.com/kker4m/linkedin-auto-applicant.git
cd linkedin-auto-applicant
```

2. Sanal ortam oluşturun ve aktifleştirin:
```bash
python -m venv venv
source venv/bin/activate  # Windows'ta: venv\Scripts\activate
```

3. Bağımlılıkları yükleyin:
```bash
pip install -r requirements.txt
```

4. `settings.json` dosyasını yapılandırmanızla oluşturun:
```json
{
    "openai_api_key": "api-anahtarınız-buraya"
}
```

### Kullanım
1. `settings.json` dosyasında ayarlarınızı yapılandırın
2. Uygulamayı çalıştırın:
```bash
python main.py
``` 