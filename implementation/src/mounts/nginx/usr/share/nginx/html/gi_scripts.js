const access_rights = {"users":"users", "system": "db"}

const API_BASE = window.location.protocol + "//" + window.location.hostname + ":10500";
const reset_key = "YES I WANT TO REsET THE DB"
const overlays = {
  "resetdb": (
    `<label for="confirmreset">Type "RESETDB" to confirm the reset </label><input type="text" id="confirmreset"><br>
    <button onclick="resetDB()">CONFIRM</button>
    <button onclick="cancelReset()">CANCEL</button>`
  ),
  "add_user": (
    `<table><tbody><tr>
        <td><label for="username">Username: </label></td>
        <td><input type="text" id="username" onfocusout="validateUserAddFields()"></td>
    </tr><tr>
        <td><label for="password">Password: </label></td>
        <td><input type="text" id="password" onfocusout="validateUserAddFields()"></td>
    </tr><tr>
        <td><label for="role">Role: </label></td>
        <td><select id="role" onfocusout="validateUserAddFields()"></select></td>
    </tr></tbody></table>
    <button onclick="okAddUser()" id="adduserbutton" disabled="disabled">ADD USER</button>
    <button onclick="cancelAddUser()" id="canceladduserbutton">CANCEL</button>`
  ),
  "add_url":(
    `<table><tbody><tr>
        <td><label for="url">URL: </label></td>
        <td><input type="text" id="url" onfocusout="validateURLAddFields()"></td>
    </tr><tr>
        <td><label for="title">Title: </label></td>
        <td><input type="text" id="title" onfocusout="validateURLAddFields()"></td>
    </tr><tr>
    </tr></tbody></table>
    <button onclick="okAddURL()" id="addurlbutton" disabled="disabled">ADD URL</button>
    <button onclick="cancelAddURL()" id="canceladdurlbutton">CANCEL</button>`
  )
}

const pages = {
  'home': async function (){
    var res = await fetch(API_BASE + '/vote/getall', {
      method: 'GET',
      credentials: 'include'
    })
    var votedata = await res.json();

    var perms = await getPermissions();
    var perms_json = await perms.json();
    renderTable(votedata, "urls",["url", "title", "totalvotes"], perms_json.permissions);
  },
  'users': async function (){
    var res = await getPermissions();
    if (! res.ok){
      navigate("home");
      return;
    }
    var perms_json = await res.json();
    if (perms_json.permissions.users === undefined){
      navigate("home");
      return;
    }
    res = await fetch(API_BASE + '/get_all_users', {
      method: 'GET',
      credentials: 'include'
    });
    var userdata = await res.json();
    renderTable(userdata, "users",["username", "role"], perms_json.permissions);
  },
  'system': async function (){
    var res = await getPermissions();
    if (! res.ok){
      console.log("Failed getting permissions");
      navigate("home");
      return;
    }
    var res_json = await res.json();
    if ((res_json.permissions.db === undefined) || (res_json.permissions.db.write != 1)){
      console.log("Issue with the JSON decoding of res: ", res_json);
      navigate("home");
      return;
    }
    document.getElementById('app').innerHTML = (
      `<div class="warning">
           <p>This will reset the database and all its contents. Proceed with caution.</p>
           <p>THIS CAN ONLY BE UNDONE BY BACKUPS!</p>
           <button id="resetdb" class="input warning" onclick="requestResetDB()">RESET DB</button>
       </div>`
    );
    document.getElementById('overlay').innerHTML = overlays.resetdb;
  }
};

const callbacks = {
  "users":{
    "add":showAddUserOverlay,
    "remove":removeSelectedUsers
  },
  "urls":{
    "add":showAddURLOverlay,
    "remove":removeSelectedURLs,
    "upvote": upvoteCallback,
    "downvote": downvoteCallback,
    "target_column":"url"
  }
}

const symbols ={
  "upvote": "+",
  "downvote": "-"
}

function renderTable(data, topic, columns, permissions) {
  const app = document.getElementById("app");
  app.innerHTML = "";
  var canWrite = (permissions[topic]["write"] == 1);
  // Container
  const container = document.createElement("div");

  // ---- Buttons (Add / Remove) ----
  if (canWrite) {
    const btnAdd = document.createElement("button");
    btnAdd.textContent = "Add";
    btnAdd.onclick = callbacks[topic]["add"];
    const btnRemove = document.createElement("button");
    btnRemove.textContent = "Remove";
    btnRemove.onclick = callbacks[topic]["remove"];

    const buttonBar = document.createElement("div");
    buttonBar.style.marginBottom = "10px";
    buttonBar.appendChild(btnAdd);
    buttonBar.appendChild(btnRemove);
    container.appendChild(buttonBar);
  }

  // ---- Table ----
  const table = document.createElement("table");
  table.border = "1";
  table.cellPadding = "6";

  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");

  // Select-all checkbox
  const thSelect = document.createElement("th");
  const checkboxAll = document.createElement("input");
  checkboxAll.type = "checkbox";
  checkboxAll.onclick = () => {
    const checks = table.querySelectorAll("tbody input[type='checkbox']");
    checks.forEach(cb => cb.checked = checkboxAll.checked);
  };
  thSelect.appendChild(checkboxAll);
  headerRow.appendChild(thSelect);

  // Column headers
  columns.forEach(col => {
    const th = document.createElement("th");
    th.textContent = col;
    headerRow.appendChild(th);
  });
  if (permissions.votes && permissions.votes.write == 1){
    ["upvote", "downvote"].forEach(col => {
      if (callbacks[topic][col] !== undefined){
        const th = document.createElement("th");
        th.textContent = symbols[col];
      }
    })
  }

  thead.appendChild(headerRow);
  table.appendChild(thead);

  // ---- Table body ----
  const tbody = document.createElement("tbody");

  (data.length > 0 ? data : [{},]).forEach(row => {
    const tr = document.createElement("tr");

    // Checkbox cell
    const tdSelect = document.createElement("td");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    tdSelect.appendChild(checkbox);
    tr.appendChild(tdSelect);

    // Data cells
    columns.forEach(col => {
      const td = document.createElement("td");
      td.textContent = row[col] !== undefined ? row[col] : "";
      td.classList.add(col + "cell");
      tr.appendChild(td);
    });

    if (permissions.votes && permissions.votes.write == 1){
      ["upvote", "downvote"].forEach(col => {
        if (callbacks[topic][col] !== undefined){
          const td = document.createElement("td");
          const btn = document.createElement("button");
          btn.textContent = symbols[col];
          btn.onclick = callbacks[topic][col](row[callbacks[topic]["target_column"]]);
          td.appendChild(btn);
          tr.appendChild(td);
        }
      })
    }

    tbody.appendChild(tr);
  });

  table.appendChild(tbody);
  container.appendChild(table);
  app.appendChild(container);
}


function buildNavBar(contents){
  const nav = document.getElementById("navigationbar")
  nav.innerHTML = `<a href="#home" onclick="navigate('home')">HOME</a>`;
  for (let [link, table] of Object.entries(access_rights)) {
    if (contents.permissions[table] === undefined){
      continue;
    }
    var a = document.createElement("a")
    a.href = `#${link}`;
    a.onclick = (dest) => { navigate(dest); };
    a.innerText = `${link.slice(0,1).toUpperCase()}${link.slice(1,link.length)} Management`;
    nav.appendChild(a);
  }
}

function authenticateUser(user, password)
{
  var token = user + ":" + password;
  var hash = btoa(token);
  return "Basic " + hash;
}

async function requestResetDB(){
  document.getElementById("overlay").style["display"] = "block";
}

async function resetDB(){
  let resetinput = document.getElementById("confirmreset");
  document.getElementById("overlay").style["display"] = "none";
  if (resetinput.value == "RESETDB"){
    const res = await fetch(
      API_BASE + '/reset_added_data', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({"key":reset_key})
      }
    );
  }
  resetinput.value = "";
}

async function cancelReset(){
  let resetinput = document.getElementById("confirmreset");
  resetinput.value = "";
  document.getElementById("overlay").style["display"] = "none";
}

async function login() {
  const username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value;
  const res = await fetch(API_BASE + '/login', {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': authenticateUser(username, password)
    }}
  );

  const data = await res;

  if (res.ok) {
    window.location.href = 'app.html';
  } else {
    document.getElementById('msg').textContent = data.message || 'Login failed.';
  }
}

async function getPermissions(){
  try{
    let res = await fetch(API_BASE + '/get_permissions', {
      method: 'GET',
      credentials: 'include'
    });

    return res;
  } catch (error){
    console.log(error);
    return {ok: false}
  }
}

function populateUserInfoTable(result_json){
  var userinfotable = document.getElementById("userinfotable");
  userinfotable.innerHTML = (
    `<table><tbody>
            <tr><th>Username: </th> <td>${result_json.username}</td></tr>
            <tr><th>Role: </th> <td>${result_json.role}</td></tr>
        </tbody></table>`
  )
}

function displaySideBar(){
  document.getElementById("userinfotab").style["display"] = "block";
  const mainarea = document.getElementById("mainarea");
  mainarea.addEventListener("click", hideSideBar);
}

function hideSideBar(){
  const sidebar = document.getElementById("userinfotab").style["display"] = "none";
  document.removeEventListener("click", hideSideBar);
}

async function checkLoggedIn(caller){
  var res =  await getPermissions();

  if ((caller == "app" ) && (!res.ok)) {
    window.location.href = 'login.html';
  }
  if ((caller == "login") && (res.ok)){
    window.location.href = 'app.html';
  }
  try{
      let result_json = await res.json();
      if (window.location.pathname == "/app.html"){
        let page = (window.location.hash || "#home").replace('#', '');
        render(page);
        buildNavBar(result_json);
        populateUserInfoTable(result_json);
      }
   }catch(error){
     console.log("Error ", error, " occured");
   }
}


function setupLoginLinsteners(){
  var username = document.getElementById("username");
  var password = document.getElementById("password");

  username.addEventListener("keydown", function (e) {
    if (e.code === "Enter") {
      tryLogin();
    }
  });
  password.addEventListener("keydown", function (e) {
    if (e.code === "Enter") {
      tryLogin();
    }
  });
}

function render(page) {
  (pages[page] || (function (){document.getElementById('app').innerHTML =  '<p>Not Found</p>';}))();
}

function navigate(page) {
  checkLoggedIn('app');
  window.location.hash = page;
  render(page);
}

function logout() {
  fetch(API_BASE + '/logout',{method:'POST',credentials:'include'})
    .then(()=> window.location='/login.html');
}

function tryLogin(){
  const username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value;
  if((username.length > 0) && (password.length > 0)){
    login();
  }
}

function showAddUserOverlay(){
  document.getElementById("overlay").innerHTML = overlays.add_user;
  const res = fetch(API_BASE + '/get_roles', {
    method: 'GET',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    }});

  res.then((value)=>{value.json().then((possible_roles) => {
    var roleselector = document.getElementById("role");
    for (var role of possible_roles){
      var e = document.createElement("option");
      e.innerHTML = role;
      e.value = role;
      roleselector.appendChild(e);
    }
    document.getElementById("overlay").style["display"] = "block";
  })},
  (cbvalue)=>{console.log("Getting roles failed. " + cbvalue.status);});
}

function validateUserAddFields(){
  var disabledOk = false;
  for (var fieldId of ["username", "password", "role"]){
    if (document.getElementById(fieldId).value.length == 0){
      disabledOk = true;
      break;
    }
  }
  document.getElementById("adduserbutton").disabled = disabledOk;
}

function okAddUser(){
  var fields = {};
  for (var fieldId of ["username", "password", "role"]){
    fields[fieldId] = document.getElementById(fieldId).value;
  }
  const res = fetch(API_BASE + '/add_user', {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(fields)}).then(
    ()=>{render("users");});
  document.getElementById("overlay").style["display"] = "none";
}

function cancelAddUser(){
  document.getElementById("overlay").style["display"] = "none";
}

function removeSelectedUsers(){
  var to_delete = [];
  var app = document.getElementById("app");
  var table = app.getElementsByTagName("table")[0];
  var tbody = table.getElementsByTagName("tbody")[0];
  var rows = tbody.getElementsByTagName("tr");
  for (var row of rows){
    var cb = row.getElementsByTagName("input")[0];
    if (cb.checked == true ){
      var username = row.getElementsByClassName("usernamecell")[0];
      to_delete.push(username.innerText);
    }
  }
  for(var user of to_delete){
    removeUser(user);
  }
}

function removeUser(username){
  fetch(API_BASE + '/delete_user', {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({"username": username})}).then(
    ()=>{render("users");},
    ()=>{render("users");});
}

function showAddURLOverlay(){
  document.getElementById("overlay").innerHTML = overlays.add_url;
  document.getElementById("overlay").style["display"] = "block";
}


function okAddURL(){
  var fields = {};
  for (var fieldId of ["url", "title"]){
    fields[fieldId] = document.getElementById(fieldId).value;
  }
  const res = fetch(API_BASE + '/url/add', {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(fields)}).then(
    ()=>{render("home");});
  document.getElementById("overlay").style["display"] = "none";
}

function cancelAddURL(){
  document.getElementById("overlay").style["display"] = "none";
}

function removeSelectedURLs(){
  var to_delete = [];
  var app = document.getElementById("app");
  var table = app.getElementsByTagName("table")[0];
  var tbody = table.getElementsByTagName("tbody")[0];
  var rows = tbody.getElementsByTagName("tr");
  for (var row of rows){
    var cb = row.getElementsByTagName("input")[0];
    if (cb.checked == true ){
      var url = row.getElementsByClassName("urlcell")[0];
      to_delete.push(url.innerText);
    }
  }
  for(url of to_delete){
    removeURL(url);
  }
}

function removeURL(url){
  fetch(API_BASE + '/url/delete', {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({"url": url})}).then(
    ()=>{render("home");},
    ()=>{render("home");});
}

function upvote(url){
  if (url == null || url.length == 0) {
    return;
  }
  fetch(API_BASE + '/vote/set/up', {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({"url": url})}).then(
    ()=>{render("home");},
    ()=>{render("home");});
}

function downvote(url){
  if (url == null || url.length == 0) {
    return;
  }
  fetch(API_BASE + '/vote/set/down', {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({"url": url})}).then(
    ()=>{render("home");},
    ()=>{render("home");});
}

function upvoteCallback(url){
  return ()=>{ upvote(url); }
}

function downvoteCallback(url){
  return ()=>{ downvote(url); }
}

function validateURLAddFields(){
  var disabledOk = false;
  for (var fieldId of ["url", "title"]){
    if (document.getElementById(fieldId).value.length == 0){
      disabledOk = true;
      break;
    }
  }
  document.getElementById("addurlbutton").disabled = disabledOk;
}
