(function () {
  const form = document.getElementById('download-form');
  const urlInput = document.getElementById('url-input');
  const submitBtn = document.getElementById('submit-btn');
  const statusBox = document.getElementById('status-box');
  const statusText = document.getElementById('status-text');
  const successBox = document.getElementById('success-box');
  const successText = document.getElementById('success-text');
  const errorBox = document.getElementById('error-box');
  const errorText = document.getElementById('error-text');

  function setLoading(on) {
    submitBtn.disabled = on;
    submitBtn.textContent = on ? '処理中...' : 'ダウンロード';
    statusBox.classList.toggle('hidden', !on);
  }

  function showError(msg) {
    errorText.textContent = msg;
    errorBox.classList.remove('hidden');
    successBox.classList.add('hidden');
  }

  function showSuccess(msg) {
    successText.textContent = msg;
    successBox.classList.remove('hidden');
    errorBox.classList.add('hidden');
  }

  function reset() {
    errorBox.classList.add('hidden');
    successBox.classList.add('hidden');
    statusBox.classList.add('hidden');
  }

  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    const url = urlInput.value.trim();
    if (!url) return;

    reset();
    setLoading(true);
    statusText.textContent = 'ページを取得して画像を収集しています...';

    let response;
    try {
      response = await fetch('/api/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
    } catch (err) {
      setLoading(false);
      showError('サーバーに接続できませんでした。');
      return;
    }

    if (!response.ok) {
      setLoading(false);
      let msg = 'エラーが発生しました。';
      try {
        const data = await response.json();
        msg = data.error || msg;
      } catch (_) {}
      showError(msg);
      return;
    }

    statusText.textContent = 'ZIPファイルを作成しています...';

    let blob;
    try {
      blob = await response.blob();
    } catch (err) {
      setLoading(false);
      showError('ZIPファイルの受信に失敗しました。');
      return;
    }

    // Derive filename from Content-Disposition or fallback
    let filename = 'images.zip';
    const cd = response.headers.get('Content-Disposition');
    if (cd) {
      const match = cd.match(/filename="?([^";\n]+)"?/i);
      if (match) filename = match[1];
    }

    const objectUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = objectUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(objectUrl);

    setLoading(false);
    showSuccess('ダウンロードが開始されました。');
  });
})();
