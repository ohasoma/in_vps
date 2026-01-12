function updateClock() {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, "0"); //2桁にそろえる 9→09
  const minutes = String(now.getMinutes()).padStart(2, "0");
  const seconds = String(now.getSeconds()).padStart(2, "0");
  document.getElementById(
    "clock"
  ).textContent = `${hours}:${minutes}:${seconds}`;
}

setInterval(updateClock, 1000); // 1秒ごとに更新
updateClock(); // 初回実行