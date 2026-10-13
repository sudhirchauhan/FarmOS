import { chromium } from 'playwright';
import { existsSync } from 'node:fs';
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH || (existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined)});
const page=await browser.newPage({viewport:{width:1440,height:1000}});
const origin=process.env.FARMOS_E2E_URL || 'http://127.0.0.1:3000';
async function post(path,data){const response=await page.request.post(origin+'/api/'+path,{data});if(!response.ok())throw new Error(await response.text());return response.json();}
const study=await post('solar-runs/',{latitude:18.52,longitude:73.86,timezone:'Asia/Kolkata',start_date:'2026-01-01',days:7,points:[{id:'open',x:0,y:0,z:0}]});
const farm=await post('farms/',{name:'Sahyadri Farm · illustrative resource study',region:'Pune, Maharashtra',area_acres:3});
const scenario=await post('scenarios/',{farm:farm.id,name:'Light + constrained resources',inputs:{start_date:'2026-01-01',beds:[{id:'annual-bed',area_m2:100}],plantings:[{
 id:'amaranth-01',bed_id:'annual-bed',crop:'Amaranth',crop_group:'leafy',area_m2:100,sowing_date:'2026-01-01',harvest_start:'2026-01-01',harvest_weeks:1,gross_yield_kg_per_m2:5,
 source_note:'Illustrative demonstration, not validated agronomy',light_response:{solar_runs:[study.id],point_id:'open',minimum_dli:5,optimum_dli:50,source_note:'Unvalidated linear response for UI demonstration'},
 daily_water_l_per_m2:2,sowing_hours_per_m2:0.1,maintenance_hours_per_m2_week:0.05,harvest_hours_per_kg:0.1}],
 resources:{water:{storage_capacity_m3:10,opening_storage_m3:0,weekly_inflow_m3:1,weekly_evaporation_m3:0.2,weekly_pumping_limit_m3:1,irrigation_efficiency:0.85},labour:{available_hours_per_week:40,fixed_hours_per_week:10,packing_hours_per_delivered_kg:0.02,delivery_hours_per_week:8}}}});
await post('scenario-runs/',{scenario:scenario.id});
await page.goto(origin);
await page.getByRole('button',{name:'View',exact:true}).first().click();
const resources=page.locator('#results details').filter({has:page.locator('summary').filter({hasText:'Weekly water and labour constraints'})});
await resources.waitFor();
await resources.evaluate(element=>{const note=document.createElement('p');note.className='notice';note.textContent='Computed resource preview · illustrative inputs, not validated agronomy. Linked light reduces potential; water/labour deficits remain explicit constraints.';element.prepend(note);});
await resources.screenshot({path:'../docs/mockups/17-linked-light-resource-constraints.jpg',type:'jpeg',quality:92});
await browser.close();
console.log('Saved calculated resource constraints JPG; illustrative scenario retained in local database.');
