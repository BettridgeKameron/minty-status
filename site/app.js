const overall = document.querySelector("#overall");
const checked = document.querySelector("#checked");
const services = document.querySelector("#services");

function serviceCard(service) {
  const card = document.createElement("article");
  card.className = `service ${service.healthy ? "up" : "down"}`;

  const heading = document.createElement("div");
  heading.className = "service-heading";

  const name = document.createElement("h2");
  name.textContent = service.name;
  const state = document.createElement("span");
  state.className = "state";
  state.textContent = service.healthy ? "Operational" : "Unavailable";
  heading.append(name, state);

  const detail = document.createElement("p");
  detail.textContent = service.healthy
    ? `${service.latency_ms} ms from GitHub`
    : service.error || "The check failed";

  card.append(heading, detail);
  return card;
}

async function refresh() {
  try {
    const response = await fetch(`status.json?t=${Date.now()}`, { cache: "no-store" });
    if (!response.ok) throw new Error("Status snapshot is unavailable");
    const snapshot = await response.json();
    const checkedAt = new Date(snapshot.checked_at);
    const stale = Date.now() - checkedAt.getTime() > 12 * 60 * 1000;

    overall.className = `overall ${stale ? "stale" : snapshot.healthy ? "up" : "down"}`;
    overall.textContent = stale
      ? "Checks are stale"
      : snapshot.healthy
        ? "All checked services are up"
        : "Some services are down";
    checked.textContent = `Last checked ${checkedAt.toLocaleString()}`;

    services.replaceChildren(...snapshot.services.map(serviceCard));
  } catch (error) {
    overall.className = "overall down";
    overall.textContent = "Status snapshot unavailable";
    checked.textContent = error.message;
  }
}

refresh();
setInterval(refresh, 60_000);
