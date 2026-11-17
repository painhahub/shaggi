/*
 * Ссылки для записи. Замените пустые значения на реальные адреса —
 * кнопки появятся автоматически, скрывать вручную ничего не нужно.
 */
const LINKS = {
  avito: "https://www.avito.ru/user/a815513ad53213c2f0973ac3fe75bea7/profile?src=sharing",
  vk: "https://vk.ru/shaggynino",
  telegram: "",                   // например: "https://t.me/sheggi_nino"
  max: "https://max.ru/join/HY7gy45X9--r2xkbTcgZcQ9OoGZ1Zv_v3VAy0oKFx7s"
};

const isValidUrl = (value) => typeof value === "string" && /^https?:\/\//i.test(value.trim());

const bookingLinks = document.getElementById("booking-links");
const buttons = Array.from(document.querySelectorAll("[data-link]"));
let visibleCount = 0;

buttons.forEach((button) => {
  const url = LINKS[button.dataset.link];

  if (!isValidUrl(url)) {
    button.remove();
    return;
  }

  button.href = url.trim();
  visibleCount += 1;
});

if (visibleCount === 1) {
  bookingLinks.classList.add("links--single");
} else if (visibleCount % 2 === 1) {
  const lastLink = bookingLinks.lastElementChild;

  if (lastLink) lastLink.classList.add("link--wide");
}

if (visibleCount === 0) {
  bookingLinks.remove();
}

document.getElementById("year").textContent = String(new Date().getFullYear());

/*
 * Прайс сложен в стопку: активная карточка сверху, за ней выглядывают края
 * следующих. Перелистывание — свайпом влево-вправо или точками под стопкой.
 * На телефоне жест горизонтальный, вертикальный скролл страницы не ломается
 * (touch-action: pan-y в стилях).
 */
const priceStack = document.getElementById("price-stack");
const priceDots = document.getElementById("price-dots");

if (priceStack && priceDots) {
  const cards = Array.from(priceStack.querySelectorAll(".price-card"));
  const swipeHint = document.getElementById("swipe-hint");

  const DEPTH_STEP = 14;        // насколько следующая карточка выглядывает снизу
  const DEPTH_SCALE = 0.04;     // и насколько она меньше активной
  const DEPTH_VISIBLE = 2;      // сколько карточек видно в стопке
  const FLICK_DISTANCE = 64;    // порог свайпа, px
  const FLICK_VELOCITY = 0.4;   // порог «броска», px/мс
  const FLICK_MIN = 24;

  let active = 0;
  const dots = [];

  const hideHint = () => {
    if (swipeHint) swipeHint.classList.add("is-hidden");
  };

  const depthTransform = (depth) =>
    `translate3d(0, ${depth * DEPTH_STEP}px, 0) scale(${1 - depth * DEPTH_SCALE})`;

  const render = (animate = true) => {
    const step = DEPTH_STEP * DEPTH_VISIBLE + 6;
    priceStack.style.height = `${cards[active].offsetHeight + step}px`;

    cards.forEach((card, index) => {
      const depth = index - active;

      card.style.transition = animate
        ? "transform 0.52s cubic-bezier(0.32, 0.72, 0, 1), opacity 0.42s ease"
        : "none";

      if (depth === 0) {
        card.style.transform = "translate3d(0, 0, 0) scale(1)";
        card.style.opacity = "1";
        card.style.zIndex = "40";
      } else if (depth > 0 && depth <= DEPTH_VISIBLE) {
        card.style.transform = depthTransform(depth);
        card.style.opacity = "1";
        card.style.zIndex = String(40 - depth * 10);
      } else if (depth > DEPTH_VISIBLE) {
        card.style.transform = depthTransform(DEPTH_VISIBLE);
        card.style.opacity = "0";
        card.style.zIndex = "5";
      } else {
        card.style.transform = "translate3d(-108%, 0, 0) rotate(-7deg)";
        card.style.opacity = "0";
        card.style.zIndex = "50";
      }
    });

    dots.forEach((dot, index) => dot.classList.toggle("is-active", index === active));
  };

  const goTo = (index) => {
    const next = Math.max(0, Math.min(cards.length - 1, index));

    if (next === active) {
      render(true);
      return;
    }

    active = next;
    hideHint();
    render(true);
  };

  cards.forEach((card, index) => {
    const dot = document.createElement("button");
    dot.type = "button";
    dot.className = "price-dot";
    dot.setAttribute("aria-label", card.querySelector(".price-card__title").textContent);
    dot.addEventListener("click", () => goTo(index));
    priceDots.append(dot);
    dots.push(dot);
  });

  let dragging = false;
  let startX = 0;
  let startTime = 0;
  let offsetX = 0;

  priceStack.addEventListener("pointerdown", (event) => {
    if (event.pointerType === "mouse" && event.button !== 0) return;

    dragging = true;
    startX = event.clientX;
    startTime = performance.now();
    offsetX = 0;
    priceStack.classList.add("is-dragging");

    cards.forEach((card) => {
      card.style.transition = "none";
    });

    priceStack.setPointerCapture(event.pointerId);
  });

  priceStack.addEventListener("pointermove", (event) => {
    if (!dragging) return;

    offsetX = event.clientX - startX;

    const card = cards[active];
    const width = priceStack.offsetWidth || 1;
    const progress = Math.min(Math.abs(offsetX) / (width * 0.55), 1);

    card.style.transform = `translate3d(${offsetX}px, 0, 0) rotate(${offsetX / 26}deg)`;

    if (offsetX < 0) {
      // Уходим к следующей: она поднимается из стопки вслед за пальцем.
      card.style.opacity = String(1 - progress * 0.7);

      const next = cards[active + 1];

      if (next) {
        next.style.zIndex = "39";
        next.style.opacity = "1";
        next.style.transform = depthTransform(1 - progress);
      }
    } else {
      // Возвращаемся назад: предыдущая выезжает из-за левого края.
      const prev = cards[active - 1];

      if (prev) {
        prev.style.zIndex = "45";
        prev.style.opacity = String(progress);
        prev.style.transform =
          `translate3d(${(progress - 1) * 100}%, ${(1 - progress) * DEPTH_STEP}px, 0) ` +
          `rotate(${(progress - 1) * 7}deg) scale(${1 - (1 - progress) * DEPTH_SCALE})`;
      }
    }
  });

  const stopDrag = () => {
    if (!dragging) return;

    dragging = false;
    priceStack.classList.remove("is-dragging");

    const elapsed = Math.max(performance.now() - startTime, 1);
    const velocity = Math.abs(offsetX) / elapsed;
    const flicked =
      Math.abs(offsetX) > FLICK_DISTANCE ||
      (velocity > FLICK_VELOCITY && Math.abs(offsetX) > FLICK_MIN);

    if (flicked && offsetX < 0 && active < cards.length - 1) {
      active += 1;
      hideHint();
    } else if (flicked && offsetX > 0 && active > 0) {
      active -= 1;
      hideHint();
    }

    offsetX = 0;
    render(true);
  };

  priceStack.addEventListener("pointerup", stopDrag);
  priceStack.addEventListener("pointercancel", stopDrag);

  priceStack.addEventListener("keydown", (event) => {
    if (event.key === "ArrowRight") {
      event.preventDefault();
      goTo(active + 1);
    } else if (event.key === "ArrowLeft") {
      event.preventDefault();
      goTo(active - 1);
    }
  });

  window.addEventListener("resize", () => render(false));

  render(false);
}
