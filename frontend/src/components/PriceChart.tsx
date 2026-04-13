import { useEffect, useRef } from 'react'
import { createChart, type IChartApi, type ISeriesApi, ColorType } from 'lightweight-charts'
import type { ChartDataPoint } from '../types'

interface Props {
  data: ChartDataPoint[]
}

export default function PriceChart({ data }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return

    // Clean up previous chart
    if (chartRef.current) {
      chartRef.current.remove()
      chartRef.current = null
    }

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#111827' },
        textColor: '#9CA3AF',
      },
      grid: {
        vertLines: { color: '#1F2937' },
        horzLines: { color: '#1F2937' },
      },
      width: containerRef.current.clientWidth,
      height: 400,
      crosshair: {
        mode: 0,
      },
      timeScale: {
        borderColor: '#374151',
        timeVisible: false,
      },
      rightPriceScale: {
        borderColor: '#374151',
      },
    })

    chartRef.current = chart

    // Candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#10B981',
      downColor: '#EF4444',
      borderDownColor: '#EF4444',
      borderUpColor: '#10B981',
      wickDownColor: '#EF4444',
      wickUpColor: '#10B981',
    })

    const candleData = data
      .filter((d) => d.open != null && d.high != null && d.low != null && d.close != null)
      .map((d) => ({
        time: d.time as string,
        open: d.open!,
        high: d.high!,
        low: d.low!,
        close: d.close!,
      }))

    candleSeries.setData(candleData as any)

    // Volume series
    const volumeSeries = chart.addHistogramSeries({
      color: '#4B5563',
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    })

    chart.priceScale('volume').applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    })

    const volumeData = data
      .filter((d) => d.volume != null)
      .map((d) => ({
        time: d.time as string,
        value: d.volume!,
        color: d.close != null && d.open != null
          ? d.close >= d.open ? '#10B98140' : '#EF444440'
          : '#4B556340',
      }))

    volumeSeries.setData(volumeData as any)

    chart.timeScale().fitContent()

    // Resize handler
    const handleResize = () => {
      if (containerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: containerRef.current.clientWidth,
        })
      }
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
      chartRef.current = null
    }
  }, [data])

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-4">
      <div ref={containerRef} />
    </div>
  )
}
