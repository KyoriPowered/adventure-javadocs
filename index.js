const API_URL = "https://api.github.com/repos/KyoriPowered/adventure-javadocs/contents";

async function getVersions(url) {
  let versions = await fetch(`${API_URL}/${url}`);
  let json = await versions.json();
  let output = "";
  for (let obj of json.reverse()) output += `<li><a href="/${obj.path}">${obj.name}</a></li>`
  return output;
}

async function load() {
  let result = await fetch(API_URL);
  let json = await result.json();
  let output = "";
  let requests = [];

  for (let obj of json) {
    if (obj.type === "dir") {
      requests.push(getVersions(obj.name).then(versions => {
        output +=
          `<div>
             <div class="header">${obj.name}</div>
             <ul>
             ${versions}
             </ul>
           </div>`
      }));
    }
  }
  await Promise.all(requests);
  document.getElementById("listContainer").innerHTML = output;
}
