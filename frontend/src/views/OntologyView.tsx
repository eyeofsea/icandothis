'use client';

import GraphViewer from '@/components/ontology/GraphViewer';

export default function OntologyView() {
  return (
    <div className="h-full w-full flex flex-col">
      <div className="px-5 pt-5 pb-3">
        <h2 className="text-lg font-bold text-white">Knowledge Graph</h2>
        <p className="text-xs text-slate-500 mt-0.5">Supply chain ontology — nodes and relationships</p>
      </div>
      <div className="flex-1 min-h-0">
        <GraphViewer />
      </div>
    </div>
  );
}
