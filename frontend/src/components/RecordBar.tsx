import { useEffect } from 'react'

interface RecordBarProps {
  active: boolean
}

export function RecordBar({ active }: RecordBarProps) {
  useEffect(() => {
    if (!active) return
    return () => {
      // état géré par le parent
    }
  }, [active])

  return (
    <div
      className={active ? 'record-bar record-bar-active' : 'record-bar'}
      role="status"
      aria-hidden={!active}
    >
      <span className="record-bar-segment" />
      <span className="record-bar-segment" />
      <span className="record-bar-segment" />
      <span className="record-bar-segment" />
      <span className="record-bar-text">
        {active ? 'Micro actif — parlez' : 'Micro inactif'}
      </span>
    </div>
  )
}