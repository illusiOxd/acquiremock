const translations = {
    uk: {
        title_checkout: "Оплата замовлення",
        to_pay: "До сплати",
        change_acc: "Змінити акаунт",
        card_label: "Номер картки",
        expiry_label: "Термін",
        cvv_label: "CVV",
        save_card: "Зберегти карту для майбутніх оплат",
        pay_btn: "Оплатити",
        enter_email: "Вхід",
        enter_email_desc: "Введіть ваш Email, щоб продовжити",
        get_code: "Отримати код",
        verify_title: "Підтвердження",
        verify_desc: "Ми надіслали код на",
        verify_btn: "Увійти",
        change_email: "Змінити Email",
        your_cards: "Ваші карти",
        history_title: "Історія транзакцій",
        success_title: "Оплата успішна!",
        success_msg: "Ваш платіж успішно оброблено. Дякуємо.",
        order_num: "Номер замовлення",
        sum_label: "Сума",
        date_label: "Дата та час",
        status_label: "Статус",
        status_paid: "Оплачено",
        return_btn: "Повернутися до магазину",
        receipt_sent: "Чек надіслано на вашу пошту",
        security_check: "Перевірка безпеки",
        security_desc: "Код підтвердження надіслано на",
        confirm_payment: "Підтвердити платіж",
        resend_code: "Надіслати код повторно"
    },
    en: {
        title_checkout: "Checkout",
        to_pay: "Total Amount",
        change_acc: "Change Account",
        card_label: "Card Number",
        expiry_label: "Expiry",
        cvv_label: "CVV",
        save_card: "Save card for future payments",
        pay_btn: "Pay",
        enter_email: "Login",
        enter_email_desc: "Enter your Email to continue",
        get_code: "Get Code",
        verify_title: "Verification",
        verify_desc: "We sent a code to",
        verify_btn: "Enter",
        change_email: "Change Email",
        your_cards: "Your Cards",
        history_title: "Transaction History",
        success_title: "Payment Successful!",
        success_msg: "Your payment has been processed successfully. Thank you.",
        order_num: "Order Number",
        sum_label: "Amount",
        date_label: "Date & Time",
        status_label: "Status",
        status_paid: "Paid",
        return_btn: "Return to Store",
        receipt_sent: "Receipt sent to your email",
        security_check: "Security Check",
        security_desc: "Verification code sent to",
        confirm_payment: "Confirm Payment",
        resend_code: "Resend Code"
    },
    de: {
        title_checkout: "Kasse",
        to_pay: "Gesamtbetrag",
        change_acc: "Konto wechseln",
        card_label: "Kartennummer",
        expiry_label: "Gültigkeit",
        cvv_label: "CVV",
        save_card: "Karte für zukünftige Zahlungen speichern",
        pay_btn: "Bezahlen",
        enter_email: "Anmeldung",
        enter_email_desc: "Geben Sie Ihre E-Mail ein",
        get_code: "Code erhalten",
        verify_title: "Bestätigung",
        verify_desc: "Code gesendet an",
        verify_btn: "Eingeben",
        change_email: "E-Mail ändern",
        your_cards: "Ihre Karten",
        history_title: "Transaktionsverlauf",
        success_title: "Zahlung erfolgreich!",
        success_msg: "Ihre Zahlung wurde erfolgreich bearbeitet. Danke.",
        order_num: "Bestellnummer",
        sum_label: "Betrag",
        date_label: "Datum & Zeit",
        status_label: "Status",
        status_paid: "Bezahlt",
        return_btn: "Zurück zum Geschäft",
        receipt_sent: "Quittung an Ihre E-Mail gesendet",
        security_check: "Sicherheitsprüfung",
        security_desc: "Bestätigungscode gesendet an",
        confirm_payment: "Zahlung bestätigen",
        resend_code: "Code erneut senden"
    },
    ru: {
        title_checkout: "Оплата заказа",
        to_pay: "К оплате",
        change_acc: "Сменить аккаунт",
        card_label: "Номер карты",
        expiry_label: "Срок",
        cvv_label: "CVV",
        save_card: "Сохранить карту",
        pay_btn: "Оплатить",
        enter_email: "Вход",
        enter_email_desc: "Введите Email для продолжения",
        get_code: "Получить код",
        verify_title: "Подтверждение",
        verify_desc: "Мы отправили код на",
        verify_btn: "Войти",
        change_email: "Сменить Email",
        your_cards: "Ваши карты",
        history_title: "История транзакций",
        success_title: "Оплата успешна!",
        success_msg: "Ваш платеж успешно обработан. Спасибо.",
        order_num: "Номер заказа",
        sum_label: "Сумма",
        date_label: "Дата и время",
        status_label: "Статус",
        status_paid: "Оплачено",
        return_btn: "Вернуться в магазин",
        receipt_sent: "Чек отправлен на вашу почту",
        security_check: "Проверка безопасности",
        security_desc: "Код подтверждения отправлен на",
        confirm_payment: "Подтвердить платеж",
        resend_code: "Отправить код повторно"
    }
};

/* --- Language Logic --- */
function changeLanguage(lang) {
    document.querySelectorAll('[data-i18n]').forEach(elem => {
        const key = elem.getAttribute('data-i18n');
        if (translations[lang] && translations[lang][key]) {
            if (elem.tagName === 'INPUT' && elem.getAttribute('placeholder')) {
                 // Optional: Translate placeholders if needed
            } else {
                elem.textContent = translations[lang][key];
            }

            // Handle Pay Button Amount
            if (key === 'pay_btn') {
                 const amount = elem.getAttribute('data-amount');
                 if(amount) {
                    elem.textContent = translations[lang][key] + ` ${amount} ₴`;
                 } else {
                    elem.textContent = translations[lang][key];
                 }
            }
        }
    });

    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.textContent.toLowerCase() === lang) btn.classList.add('active');
    });

    localStorage.setItem('selectedLang', lang);
}

function toggleTheme() {
    const body = document.body;
    body.classList.toggle('dark-mode');

    const isDark = body.classList.contains('dark-mode');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    updateThemeIcon(isDark);
}

function updateThemeIcon(isDark) {
    const sun = document.querySelector('.sun-icon');
    const moon = document.querySelector('.moon-icon');

    // Safety check if icons exist on page
    if (!sun || !moon) return;

    if (isDark) {
        sun.style.display = 'block';
        moon.style.display = 'none';
    } else {
        sun.style.display = 'none';
        moon.style.display = 'block';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const savedLang = localStorage.getItem('selectedLang') || 'uk';
    changeLanguage(savedLang);

    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        updateThemeIcon(true);
    } else {
        updateThemeIcon(false);
    }
});