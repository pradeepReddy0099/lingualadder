// headless smoke: run app.js with a fake DOM against en.json
const fs=require('fs');global.window={};global.performance={now:()=>0};
const els={};const mk=id=>els[id]||(els[id]={id,value:'',checked:false,textContent:'',innerHTML:'',className:'',options:[],addEventListener(){},focus(){},select(){}});
global.document={getElementById:mk,addEventListener(){},body:{classList:{toggle(){}}}};
global.localStorage={getItem:()=>null,setItem(){}};global.location={search:'',href:'http://x/'};global.history={replaceState(){}};
global.URLSearchParams=URLSearchParams;
global.fetch=async u=>({ok:true,json:async()=>JSON.parse(fs.readFileSync(__dirname+'/'+u))});
global.LL=require(__dirname+'/ll.js');
eval(fs.readFileSync(__dirname+'/app.js','utf8')+'\n;global.run=run;');
mk('q').value='volcano';mk('lang').value='en';mk('level').value='beginner';
run().then(()=>{console.log('status:',els.status.textContent);console.log('html len',els.results.innerHTML.length)}).catch(e=>console.log('ERR',e.message));
