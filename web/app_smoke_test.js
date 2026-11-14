// headless smoke: run app.js with a fake DOM against en.json
const fs=require('fs');global.window={};global.performance={now:()=>0};
const els={};const mk=id=>els[id]||(els[id]={id,value:'',checked:false,textContent:'',innerHTML:'',className:'',options:[],dataset:{},style:{},querySelectorAll:()=>[],addEventListener(){},focus(){},select(){}});
global.document={getElementById:mk,querySelectorAll:()=>[],addEventListener(){},body:{classList:{toggle(){},add(){}}}};
global.localStorage={getItem:()=>null,setItem(){}};global.location={search:'',href:'http://x/'};global.history={replaceState(){}};
global.URLSearchParams=URLSearchParams;
global.fetch=async u=>({ok:true,json:async()=>JSON.parse(fs.readFileSync(__dirname+'/'+u))});
global.LLI18n=require(__dirname+'/i18n.js');global.LL=require(__dirname+'/ll.js');global.LLPlace=require(__dirname+'/placement.js');
eval(fs.readFileSync(__dirname+'/app.js','utf8')+'\n;global.run=run;global.renderTopics=renderTopics;');
const UI=process.argv[2]||'en',LANG=process.argv[3]||'en',QQ=process.argv[4]||'volcano';LLI18n.set(UI);
mk('q').value=QQ;mk('lang').value=LANG;mk('level').value='beginner';
run().then(()=>renderTopics()).then(()=>{console.log('status:',els.status.textContent);console.log('html len',els.results.innerHTML.length);console.log('ladder:',/ladder-strip/.test(els.results.innerHTML));setTimeout(()=>console.log('topics:',(els.topics.innerHTML.match(/data-topic="([^"]+)"/g)||[]).slice(0,6).join(' ')),50)}).catch(e=>console.log('ERR',e.message));
