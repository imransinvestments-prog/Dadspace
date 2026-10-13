/* Shared decision validation; no database connection or network writes. */
(function(root){
const allowed={split:['split','defer','withdraw'],routes:['repair','split','defer','withdraw'],venue:['venue','defer'],mobile:['mobile','defer','withdraw']};
function url(value){try{const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password&&(!u.port||u.port==='443')}catch(e){return false}}
function validate(record,d){
 const errors=[]; const need=(v,msg)=>{if(!String(v||'').trim())errors.push(msg)};
 if(!allowed[record.group].includes(d.action))errors.push('Choose an action.');
 need(d.reviewer,'Enter the reviewer name.');
 if(!d.reviewed)errors.push('Confirm you checked the evidence.');
 if(d.action==='defer'){need(d.notes,'Record what is missing and the next step.');return errors;}
 if(!url(d.evidence_url))errors.push('Add a valid HTTPS evidence link.');
 if(d.action==='split'){
   if(!Array.isArray(d.sessions)||!d.sessions.length)errors.push('Add at least one individual session.');
   for(const [i,s] of (d.sessions||[]).entries()){
     const label='Session '+(i+1)+': ';
     for(const [k,n] of [['name','name'],['venue','venue'],['location','address or location'],['ages','published ages'],['schedule','published schedule or selected dates']])need(s[k],label+'enter '+n+'.');
     if(!url(s.evidence_url))errors.push(label+'add a valid HTTPS evidence link.');
     if(s.booking_url&&!url(s.booking_url))errors.push(label+'booking link must be HTTPS.');
     if(/time to confirm|time tbc|time unknown/i.test(String(s.schedule||'')))errors.push(label+'replace the unknown-time placeholder with the evidenced session time before marking ready.');
     const dates=String(s.dates||'').split(/[\s,;]+/).filter(Boolean);
     if(dates.some(x=>!/^\d{4}-\d{2}-\d{2}$/.test(x)||Number.isNaN(Date.parse(x+'T12:00:00Z'))||new Date(x+'T12:00:00Z').toISOString().slice(0,10)!==x))errors.push(label+'use actual published dates in YYYY-MM-DD format.');
   }
 }
 if(d.action==='repair'&&!url(d.replacement_url))errors.push('Enter the verified replacement HTTPS route.');
 if(d.action==='withdraw')need(d.notes,'Give the closure/expiry evidence and withdrawal reason; a 404 alone is insufficient.');
 if(d.action==='venue'){need(d.venue_name,'Enter the place name.');need(d.venue_location,'Enter its location.');if(d.canonical_venue_id&&!/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i.test(d.canonical_venue_id))errors.push('Canonical venue ID must be a UUID, or left blank for matching.');}
 if(d.action==='mobile'){need(d.service_area,'Enter the service area.');need(d.availability,'Explain how appointments are arranged.');if(!url(d.booking_url))errors.push('Enter a valid HTTPS booking/contact route.');}
 return errors;
}
function importDecisions(payload,data){
 if(payload.version!==data.version||payload.cohort!==data.cohort||!Array.isArray(payload.decisions))throw Error('This file belongs to a different review or format.');
 const byId=new Map(data.records.map(r=>[r.id,r])),result={};
 for(const d of payload.decisions){
   const r=byId.get(d?.record_id);if(!r||result[d.record_id])throw Error('Unknown or duplicate record ID.');
   if(d.expected_fingerprint!==r.fingerprint)throw Error('Record snapshot does not match this worksheet.');
   if(!['draft','ready'].includes(d.status)||!allowed[r.group].includes(d.action))throw Error('Unknown decision status or action.');
   if(!Array.isArray(d.sessions)||d.sessions.some(s=>!s||typeof s!=='object'||Object.values(s).some(v=>typeof v!=='string')))throw Error('Invalid session form data.');
   if(typeof d.reviewed!=='boolean')throw Error('Invalid evidence confirmation.');
   const cleaned={record_id:d.record_id,expected_fingerprint:r.fingerprint,status:d.status,action:d.action,reviewed:d.reviewed,sessions:d.sessions};
   for(const k of ['reviewer','evidence_url','notes','replacement_url','venue_name','venue_location','canonical_venue_id','service_area','availability','booking_url','updated_at','reviewed_at']){
     if(d[k]!==undefined&&typeof d[k]!=='string')throw Error('Invalid text field.');cleaned[k]=d[k]||'';
   }
   if(d.status==='ready'&&validate(r,cleaned).length)throw Error('Ready decision has missing or invalid fields.');result[d.record_id]=cleaned;
 }
 return result;
}
const api={allowed,url,validate,importDecisions};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.DadspaceDecisions=api;
})(typeof window!=='undefined'?window:globalThis);
